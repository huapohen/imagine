#!/usr/bin/env bash
set -euo pipefail
PITCH_ROOT="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$PITCH_ROOT")"
TASK_RUNTIME='/Users/lwblx/.cache/codex-runtimes/codex-primary-runtime'
TASK_NODE="$TASK_RUNTIME/dependencies/node/bin/node"
TASK_PYTHON="$TASK_RUNTIME/dependencies/python/bin/python3"
TASK_RUN="${1:-$(date +%Y%m%d-%H%M%S)}"
if [[ ! "$TASK_RUN" =~ ^[A-Za-z0-9_-]+$ ]]; then echo 'Version must contain only letters, digits, underscore or hyphen.' >&2; exit 1; fi
if [[ -e "$PITCH_ROOT/deliverables/$TASK_RUN/lingban-vc-deck.pptx" ]]; then echo 'Choose a new version; finalized outputs are never overwritten.' >&2; exit 1; fi
cd "$REPO_ROOT"
mkdir -p "$PITCH_ROOT/.build" "$PITCH_ROOT/deliverables/$TASK_RUN"
if [[ ! -e "$PITCH_ROOT/.build/node_modules" ]]; then ln -s "$TASK_RUNTIME/dependencies/node/node_modules" "$PITCH_ROOT/.build/node_modules"; fi
cp "$PITCH_ROOT/src/build.mjs" "$PITCH_ROOT/.build/build.mjs"
cp "$PITCH_ROOT/src/verify-html.mjs" "$PITCH_ROOT/.build/verify-html.mjs"
cat > "$PITCH_ROOT/.build/fonts.conf" <<FONTCONF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig><dir>/System/Library/Fonts</dir><dir>/System/Library/Fonts/Supplemental</dir><dir>$TASK_RUNTIME/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype</dir><cachedir>$PITCH_ROOT/.build/font-cache</cachedir><alias><family>sans-serif</family><prefer><family>Hiragino Sans GB</family></prefer></alias></fontconfig>
FONTCONF
"$TASK_NODE" "$PITCH_ROOT/.build/build.mjs" "$TASK_RUN"
FONTCONFIG_FILE="$PITCH_ROOT/.build/fonts.conf" "$TASK_RUNTIME/dependencies/bin/override/soffice" "-env:UserInstallation=file://$PITCH_ROOT/.build/lo-font-profile" --headless --convert-to pdf --outdir "$PITCH_ROOT/deliverables/$TASK_RUN" "$PITCH_ROOT/deliverables/$TASK_RUN/lingban-vc-deck.pptx"
mkdir -p "$PITCH_ROOT/.build/$TASK_RUN/render"
"$TASK_RUNTIME/dependencies/bin/override/pdftoppm" -scale-to 1600 -png "$PITCH_ROOT/deliverables/$TASK_RUN/lingban-vc-deck.pdf" "$PITCH_ROOT/.build/$TASK_RUN/render/slide"
"$TASK_PYTHON" "$PITCH_ROOT/src/postprocess.py" "$TASK_RUN"
"$TASK_NODE" "$PITCH_ROOT/.build/verify-html.mjs" "$TASK_RUN"
"$TASK_PYTHON" - "$PITCH_ROOT/.build/$TASK_RUN/html-print-check.pdf" <<'PY'
import sys
from pypdf import PdfReader
assert len(PdfReader(sys.argv[1]).pages)==18
print('HTML print: 18 pages verified')
PY
echo "Built: $PITCH_ROOT/deliverables/$TASK_RUN"
echo "Review every rendered page before selecting a new release."
