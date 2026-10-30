import * as vscode from 'vscode';

interface SecretResult {
  candidate_string: string;
  secret_type: string;
  is_secret: boolean;
  position_start: number;
  position_end: number;
  pattern_id: string;
}

interface DetectionResponse {
  success: boolean;
  secrets_detected: number;
  secrets: SecretResult[];
}

const decorationType = vscode.window.createTextEditorDecorationType({
  backgroundColor: 'rgba(255,0,0,0.25)',
  border: '1px solid red',
  rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed,
});

let activeDecorationRanges: vscode.Range[] = [];

export function activate(context: vscode.ExtensionContext) {
  const editorDisposable = vscode.workspace.onDidChangeTextDocument(event => {
    for (const change of event.contentChanges) {
      if (isLikelyPaste(change)) {
        checkForSecrets(change.text, event.document, change.range.start);
      }
    }
  });
  context.subscriptions.push(editorDisposable);

  startCommitBoxPolling(context);
}

let lastCommitMessage = '';
let commitDebounceTimer: NodeJS.Timeout | undefined;

function startCommitBoxPolling(context: vscode.ExtensionContext) {
  const gitExtension = vscode.extensions.getExtension('vscode.git')?.exports;
  const gitApi = gitExtension?.getAPI(1);

  const pollInterval = setInterval(() => {
    const repo = gitApi?.repositories[0];
    if (!repo) return;

    const currentMessage: string = repo.inputBox.value;
    if (currentMessage !== lastCommitMessage) {
      lastCommitMessage = currentMessage;
      if (commitDebounceTimer) clearTimeout(commitDebounceTimer);
      commitDebounceTimer = setTimeout(() => {
        if (currentMessage.trim().length > 0) {
          checkCommitMessageForSecrets(currentMessage);
        }
      }, 500);
    }
  }, 300); // check the box 3-4 times a second — cheap, and nothing user-visible depends on sub-second timing here

  context.subscriptions.push({ dispose: () => clearInterval(pollInterval) });
}

async function checkCommitMessageForSecrets(text: string) {
  const response = await fetch('http://localhost:8000/detect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, max_results: 10, batch_size: 1 }),
  });
  const result = (await response.json()) as DetectionResponse;

  if (result.success && result.secrets_detected > 0) {
    vscode.window.showWarningMessage(
      `Possible secret in commit message: ${result.secrets.length} match(es) (${result.secrets.map(s => s.secret_type).join(', ')}).`
    );
  }
}

function isLikelyPaste(change: vscode.TextDocumentContentChangeEvent): boolean {
  const insertedLength = change.text.length;
  const isPureInsertion = change.rangeLength === 0;
  const isBulkInsert = insertedLength > 15;
  const hasNewline = change.text.includes('\n');
  return isPureInsertion && (isBulkInsert || hasNewline);
}

// --- Step 2.2: comment extraction, defined but not currently used —
// checkForSecrets below scans the full pasted text, not just comments.
// Call extractComments(text, document.languageId) inside checkForSecrets
// if you decide later you want detection scoped to comments only.
const commentPatterns: Record<string, RegExp> = {
  javascript: /\/\/.*$|\/\*[\s\S]*?\*\//gm,
  typescript: /\/\/.*$|\/\*[\s\S]*?\*\//gm,
  python: /#.*$/gm,
  java: /\/\/.*$|\/\*[\s\S]*?\*\//gm,
};

function extractComments(text: string, languageId: string): string {
  const pattern = commentPatterns[languageId];
  if (!pattern) return text; // unsupported language — fall back to scanning everything
  return (text.match(pattern) || []).join('\n');
}

async function checkForSecrets(text: string, document: vscode.TextDocument, position: vscode.Position) {
  const response = await fetch('http://localhost:8000/detect', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, max_results: 10, batch_size: 1 }),
  });
  const result = (await response.json()) as DetectionResponse;

  if (result.success && result.secrets_detected > 0) {
    showWarning(document, position, result.secrets);
  }
}

function showWarning(document: vscode.TextDocument, position: vscode.Position, secrets: SecretResult[]) {
  vscode.window.showWarningMessage(
    `Possible secret detected: ${secrets.length} match(es) in pasted text (${secrets.map(s => s.secret_type).join(', ')}).`
  );

  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document !== document) return;

  const newRanges = secrets.map(s => {
    const start = document.positionAt(document.offsetAt(position) + s.position_start);
    const end = document.positionAt(document.offsetAt(position) + s.position_end);
    return new vscode.Range(start, end);
  });

  activeDecorationRanges = [...activeDecorationRanges, ...newRanges];
  editor.setDecorations(decorationType, activeDecorationRanges);
}

export function deactivate() {}