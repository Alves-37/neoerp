from __future__ import annotations

from pathlib import Path

from app.settings import Settings


def main() -> None:
    settings = Settings()
    p = Path(settings.upload_dir).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)

    probe = p / ".write_test"
    probe.write_text("ok", encoding="utf-8")
    probe.unlink(missing_ok=True)

    print(f"UPLOAD_DIR ok: {p}")


if __name__ == "__main__":
    main()
