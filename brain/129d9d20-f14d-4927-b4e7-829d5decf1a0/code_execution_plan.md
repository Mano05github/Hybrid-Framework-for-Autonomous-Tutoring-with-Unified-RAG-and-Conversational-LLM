# Phase 5: Code Execution Engine (Pyodide Strategy)

## Goal
Enable the "Run" button in the Code Editor to execute Python code instantly within the browser.

## Strategy: Client-Side (Pyodide)
We will use **Pyodide** (WASM-based Python) because:
1.  **Zero Latency**: Runs on the user's machine.
2.  **Safety**: Sandboxed in the browser (cannot harm the server).
3.  **Simplicity**: No complex Docker/Backend Sandbox required for this MVP.

## Implementation Steps

### 1. Setup Pyodide in Next.js
*   Since Pyodide is large (~10MB), we load it asynchronously.
*   We need a `Script` tag or a custom Hook `usePyodide`.

### 2. Output Capturing
*   By default, Pyodide writes to the browser console.
*   We must divert `sys.stdout` and `sys.stderr` to a JavaScript buffer so we can display it in our `Terminal` component.

### 3. Integration with `EmbeddedCodeEditor`
*   Add a "Terminal" pane at the bottom of the editor.
*   On "Run" click:
    1.  Clear previous output.
    2.  Send code string to Pyodide.
    3.  Await result.
    4.  Print stdout + return value.

### 4. Security Note
*   While Pyodide is safe from the server perspective, we should warn users about infinite loops (browser freeze).
*   *Future*: Implement a WebWorker to run it off the main thread (prevents UI freezing).

## Tech Stack
*   `pyodide` (via CDN or npm)
*   `react-console-emulator` (optional, or custom UI)
