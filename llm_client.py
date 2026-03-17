from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from .prompts import CHAT_PROMPT, MIDI_AGENT_PROMPT


def _env_bool(key: str, default: bool) -> bool:
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class LLMContext:
    bar: int
    bpm: int
    meter_num: int
    style: str = "simple piano"
    regen_hint: str = ""
    attempt: int = 1
    bars_to_generate: int = 1
    allow_end_signal: bool = False


class LLMClient:
    """LLM wrapper with provider switch and safe offline stub fallback."""

    def __init__(self, model: str = "gpt-4o-mini", use_stub: bool | None = None):
        self.provider = os.getenv("LLM_PROVIDER", "openai").strip().lower()
        if self.provider not in {"openai", "gemini", "ollama"}:
            print(f"[llm] unknown provider={self.provider}, fallback to openai")
            self.provider = "openai"

        if self.provider == "openai":
            default_model = model
            model_env_key = "OPENAI_MODEL"
            api_env_key = "OPENAI_API_KEY"
        elif self.provider == "gemini":
            default_model = "gemini-2.5-flash"
            model_env_key = "GEMINI_MODEL"
            api_env_key = "GEMINI_API_KEY"
        else:
            default_model = "qwen2.5:7b-instruct"
            model_env_key = "OLLAMA_MODEL"
            api_env_key = ""

        self.model = os.getenv(model_env_key, default_model)
        self.api_key = os.getenv(api_env_key, "") if api_env_key else ""
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
        self.raw_log_path = os.getenv("LLM_RAW_LOG_PATH", "").strip()
        self.echo_io = _env_bool("LLM_ECHO_IO", True)
        self._ollama_cached_models: list[str] | None = None
        self.run_id = os.getenv("MIDI_AGENT_RUN_ID", f"run-{int(time.time())}")
        self._seq = 0
        self.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "2"))
        self.request_timeout = float(os.getenv("OPENAI_TIMEOUT_SEC", "20"))
        if use_stub is None:
            if self.provider in {"openai", "gemini"}:
                use_stub = not bool(self.api_key)
            else:
                # Local Ollama does not require API key.
                use_stub = False
        self.use_stub = use_stub
        self._client = None

        if not self.use_stub and self.provider == "openai":
            try:
                from openai import OpenAI

                self._client = OpenAI()
            except Exception:
                self.use_stub = True

        if self.use_stub:
            print(
                f"[llm] running in stub mode (provider={self.provider}, "
                f"missing key/client unavailable)"
            )
        else:
            print(
                f"[llm] provider={self.provider} model={self.model} retries={self.max_retries} "
                f"timeout={self.request_timeout}s run_id={self.run_id}"
            )

    def chat(self, user_text: str) -> str:
        if self.use_stub:
            return f"[stub-chat] {user_text}"
        try:
            out = self._generate_text(CHAT_PROMPT, user_text, temperature=0.5)
            self._log_raw(
                kind="chat",
                system_prompt=CHAT_PROMPT,
                user_prompt=user_text,
                output_text=out,
                error=None,
            )
            return out
        except Exception as exc:
            self._log_raw(
                kind="chat",
                system_prompt=CHAT_PROMPT,
                user_prompt=user_text,
                output_text="",
                error=str(exc),
            )
            raise

    def generate_chunk(self, context: LLMContext) -> str:
        return self.generate_chunks(context)

    def generate_chunks(self, context: LLMContext) -> str:
        if self.use_stub:
            return self._stub_chunks(context)

        to_bar = context.bar + max(1, int(context.bars_to_generate)) - 1
        user_prompt = (
            f"bar={context.bar}, bpm={context.bpm}, meter={context.meter_num}/4, "
            f"style={context.style}. {context.regen_hint}\n"
            f"Generate bar chunks from from_bar={context.bar} to to_bar={to_bar}.\n"
            "Hard constraints: each chunk is one bar only (4 beats), 0<=t<4, d>0, t+d<=4, "
            "t and d are decimal multiples of 0.25, notes list must use commas.\n"
            "Output one @chunk...@eochunk block per bar, in ascending bar order, no extra text."
        )
        if context.allow_end_signal:
            user_prompt += "\nIf you decide composition should end after the final chunk, append a final line: @end"
        try:
            out = self._generate_text(MIDI_AGENT_PROMPT, user_prompt, temperature=0.3).strip()
            self._log_raw(
                kind="chunk",
                system_prompt=MIDI_AGENT_PROMPT,
                user_prompt=user_prompt,
                output_text=out,
                error=None,
                meta={
                    "bar": context.bar,
                    "to_bar": to_bar,
                    "bars_to_generate": context.bars_to_generate,
                    "allow_end_signal": context.allow_end_signal,
                    "style": context.style,
                    "attempt": context.attempt,
                },
            )
            return out
        except Exception as exc:
            self._log_raw(
                kind="chunk",
                system_prompt=MIDI_AGENT_PROMPT,
                user_prompt=user_prompt,
                output_text="",
                error=str(exc),
                meta={
                    "bar": context.bar,
                    "to_bar": to_bar,
                    "bars_to_generate": context.bars_to_generate,
                    "allow_end_signal": context.allow_end_signal,
                    "style": context.style,
                    "attempt": context.attempt,
                },
            )
            raise

    def _generate_text(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if self.provider == "openai":
            resp = self._responses_create(
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
            )
            return getattr(resp, "output_text", "") or ""
        if self.provider == "gemini":
            return self._gemini_generate(system_prompt, user_prompt, temperature)
        return self._ollama_generate(system_prompt, user_prompt, temperature)

    def _responses_create(self, **kwargs):
        if self._client is None:
            raise RuntimeError("OpenAI client not initialized")
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._client.responses.create(
                    model=self.model,
                    timeout=self.request_timeout,
                    **kwargs,
                )
            except Exception as exc:
                last_exc = exc
                # Deterministic bad-request errors should fail fast.
                code = getattr(exc, "code", None)
                if code in {"model_not_found", "invalid_api_key", "insufficient_quota"}:
                    raise RuntimeError(f"OpenAI request invalid: {exc}") from exc
                if attempt >= self.max_retries:
                    break
                backoff = 0.25 * (2**attempt)
                print(
                    f"[llm] request failed attempt={attempt + 1}/{self.max_retries + 1} "
                    f"error={type(exc).__name__}: {exc} retry_in={backoff:.2f}s"
                )
                time.sleep(backoff)
        raise RuntimeError(f"LLM request failed after retries: {last_exc}") from last_exc

    def _gemini_generate(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if not self.api_key:
            raise RuntimeError("Gemini API key missing: set GEMINI_API_KEY")

        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                url = (
                    "https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{self.model}:generateContent"
                )
                payload = {
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "generationConfig": {"temperature": temperature},
                }
                req = urllib.request.Request(
                    url=url,
                    data=json.dumps(payload).encode("utf-8"),
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    },
                )
                with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                    body = resp.read().decode("utf-8")
                data = json.loads(body)
                cands = data.get("candidates", [])
                if not cands:
                    raise RuntimeError(f"Gemini empty response: {body[:300]}")
                parts = cands[0].get("content", {}).get("parts", [])
                text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
                if not text.strip():
                    raise RuntimeError(f"Gemini no text content: {body[:300]}")
                return text
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                body_l = body.lower()
                # Deterministic config errors should fail fast.
                if exc.code in {400, 404} and (
                    "not found" in body_l
                    or "api key" in body_l
                    or "permission" in body_l
                    or "unsupported" in body_l
                ):
                    if "not found" in body_l or "unsupported" in body_l:
                        raise RuntimeError(
                            "Gemini model invalid/unsupported for generateContent. "
                            f"Current GEMINI_MODEL={self.model}. "
                            "Try GEMINI_MODEL=gemini-2.5-flash or check ListModels."
                        ) from exc
                    raise RuntimeError(f"Gemini request invalid: HTTP {exc.code}: {body[:300]}") from exc
                last_exc = RuntimeError(f"HTTP {exc.code}: {body[:300]}")
            except Exception as exc:
                last_exc = exc

            if attempt >= self.max_retries:
                break
            backoff = 0.25 * (2**attempt)
            print(
                f"[llm] request failed attempt={attempt + 1}/{self.max_retries + 1} "
                f"error={type(last_exc).__name__}: {last_exc} retry_in={backoff:.2f}s"
            )
            time.sleep(backoff)

        raise RuntimeError(f"Gemini request failed after retries: {last_exc}") from last_exc

    def _ollama_generate(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                url = f"{self.ollama_base_url}/api/generate"
                payload = {
                    "model": self.model,
                    "prompt": f"[SYSTEM]\n{system_prompt}\n\n[USER]\n{user_prompt}",
                    "stream": False,
                    "options": {"temperature": temperature},
                }
                req = urllib.request.Request(
                    url=url,
                    data=json.dumps(payload).encode("utf-8"),
                    method="POST",
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                    body = resp.read().decode("utf-8")
                data = json.loads(body)
                if data.get("error"):
                    raise RuntimeError(str(data["error"]))
                text = (data.get("response") or "").strip()
                if not text:
                    raise RuntimeError(f"Ollama empty response: {body[:300]}")
                return text
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                body_l = body.lower()
                if exc.code in {400, 404} and ("not found" in body_l or "pull" in body_l):
                    available = self._ollama_list_models()
                    available_text = ", ".join(available[:12]) if available else "unavailable"
                    raise RuntimeError(
                        f"Ollama model not found: {self.model}. "
                        f"Local models: {available_text}. "
                        f"Run: ollama pull {self.model}"
                    ) from exc
                last_exc = RuntimeError(f"HTTP {exc.code}: {body[:300]}")
            except Exception as exc:
                last_exc = exc

            if attempt >= self.max_retries:
                break
            backoff = 0.25 * (2**attempt)
            print(
                f"[llm] request failed attempt={attempt + 1}/{self.max_retries + 1} "
                f"error={type(last_exc).__name__}: {last_exc} retry_in={backoff:.2f}s"
            )
            time.sleep(backoff)

        raise RuntimeError(f"Ollama request failed after retries: {last_exc}") from last_exc

    def _ollama_list_models(self) -> list[str]:
        if self._ollama_cached_models is not None:
            return self._ollama_cached_models
        try:
            url = f"{self.ollama_base_url}/api/tags"
            req = urllib.request.Request(
                url=url,
                method="GET",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=self.request_timeout) as resp:
                body = resp.read().decode("utf-8")
            data = json.loads(body)
            models = data.get("models", [])
            names = [
                m.get("name", "").strip()
                for m in models
                if isinstance(m, dict) and m.get("name")
            ]
            self._ollama_cached_models = names
            return names
        except Exception:
            self._ollama_cached_models = []
            return []

    def _log_raw(
        self,
        kind: str,
        system_prompt: str,
        user_prompt: str,
        output_text: str,
        error: str | None,
        meta: dict | None = None,
    ) -> None:
        if not self.raw_log_path:
            return
        self._seq += 1
        record = {
            "timestamp": time.time(),
            "run_id": self.run_id,
            "seq": self._seq,
            "provider": self.provider,
            "model": self.model,
            "kind": kind,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "output_text": output_text,
            "error": error,
            "meta": meta or {},
        }
        if self.echo_io:
            self._echo_record(record)
        try:
            with open(self.raw_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception:
            # Logging must never break playback/chat flow.
            pass

    @staticmethod
    def _echo_record(record: dict) -> None:
        kind = record.get("kind")
        seq = record.get("seq")
        bar = record.get("meta", {}).get("bar")
        attempt = record.get("meta", {}).get("attempt")
        provider = record.get("provider")
        model = record.get("model")
        err = record.get("error")
        print("")
        print(f"[llm-io] BEGIN kind={kind} seq={seq} bar={bar} attempt={attempt}")
        print(f"[llm-io] provider={provider} model={model}")
        print("[llm-io] --- system_prompt ---")
        print(record.get("system_prompt", ""))
        print("[llm-io] --- user_prompt ---")
        print(record.get("user_prompt", ""))
        print("[llm-io] --- output_text ---")
        print(record.get("output_text", ""))
        if err:
            print("[llm-io] --- error ---")
            print(err)
        print("[llm-io] END")
        print("")

    @staticmethod
    def _stub_chunks(context: LLMContext) -> str:
        # 4/4 bar, grid 1/16 -> 0.25 beat. simple arpeggio + chord hit.
        lines: list[str] = []
        for bar in range(context.bar, context.bar + max(1, int(context.bars_to_generate))):
            root = [60, 62, 65, 67][bar % 4]
            lines.append(f"@chunk from_bar={bar} to_bar={bar}")
            lines.append(f"t=0.00 d=1.00 notes=[{root},{root+4},{root+7}] v=80")
            lines.append(f"t=1.00 d=1.00 notes=[{root+12}] v=86")
            lines.append(f"t=2.00 d=1.00 notes=[{root+7}] v=82")
            lines.append(f"t=3.00 d=1.00 notes=[{root+4}] v=82")
            lines.append("@eochunk")
        return "\n".join(lines)
