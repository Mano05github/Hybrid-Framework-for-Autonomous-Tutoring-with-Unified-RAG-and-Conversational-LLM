# Plan: Hand-Drawn "Canvas Board" Layout

## Goal
Implement the specific UI layout sketched by the user.
**Layout**: Split Screen.
*   **Left Panel**: Voice Assistant.
*   **Right Panel**: Infinite Canvas (Whiteboard).

## Proposed Changes

### 1. Page Layout ([learn/[lessonId]/page.tsx](file:///d:/final%20year%20project/V/frontend/app/learn/[lessonId]/page.tsx))
*   Revert to Flex Row layout.
*   **Left Container**: Width 20-25% (Visuals/Controls).
*   **Right Container**: Width 75-80% (Canvas).

### 2. Voice Assistant Panel ([VoiceAgentVisual.tsx](file:///d:/final%20year%20project/V/frontend/components/learning-session/VoiceAgentVisual.tsx))
*   **Location**: Occupies the entire Left Panel.
*   **Content**:
    *   Header: "Assistant"
    *   Visualizer: "Voice Assistant Symbol" (4 dots / wave animation).
    *   Controls: Mic and Hand buttons as drawn.

### 3. Whiteboard Canvas ([WhiteboardCanvas.tsx](file:///d:/final%20year%20project/V/frontend/components/learning-session/WhiteboardCanvas.tsx))
*   **Behavior**: Infinite Pan/Zoom (Keep existing logic).
*   **Toolbar**: Implement the **Floating Tool Manager** inside the canvas.
    *   **Tools**: Cursor, Pencil, Eraser, Color Picker.
    *   **Style**: Floating capsule/bar as drawn in the sketch.

## Verification
*   **Visual Check**: Does it match the sketch?
    *   Left: Assistant Panel.
    *   Right: Canvas.
    *   Floating Toolbar: Visible on Canvas.
