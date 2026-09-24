/**
 * Custom Cursor - Cinematic Effect
 * ================================
 * Shared cursor animation for all learning pages
 */

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initCursor);
    } else {
        initCursor();
    }
    
    function initCursor() {
        // Check if cursor elements already exist
        if (document.querySelector('.cursor-dot')) return;
        
        // Create cursor elements
        const cursorDot = document.createElement('div');
        cursorDot.className = 'cursor-dot';
        
        const cursorOutline = document.createElement('div');
        cursorOutline.className = 'cursor-outline';
        
        document.body.appendChild(cursorDot);
        document.body.appendChild(cursorOutline);
        
        // Track mouse position
        let mouseX = 0;
        let mouseY = 0;
        let outlineX = 0;
        let outlineY = 0;
        
        // Update mouse position
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            
            // Update dot immediately
            cursorDot.style.left = `${mouseX}px`;
            cursorDot.style.top = `${mouseY}px`;
        });
        
        // Smooth outline animation
        function animateOutline() {
            // Lerp (linear interpolation) for smooth following
            outlineX += (mouseX - outlineX) * 0.15;
            outlineY += (mouseY - outlineY) * 0.15;
            
            cursorOutline.style.left = `${outlineX}px`;
            cursorOutline.style.top = `${outlineY}px`;
            
            requestAnimationFrame(animateOutline);
        }
        
        animateOutline();
        
        // Expand cursor on interactive elements
        const interactiveElements = 'a, button, input, textarea, select, [role="button"], .btn';
        
        document.addEventListener('mouseover', (e) => {
            if (e.target.matches(interactiveElements)) {
                cursorOutline.style.width = '60px';
                cursorOutline.style.height = '60px';
            }
        });
        
        document.addEventListener('mouseout', (e) => {
            if (e.target.matches(interactiveElements)) {
                cursorOutline.style.width = '40px';
                cursorOutline.style.height = '40px';
            }
        });
        
        // Hide cursor when leaving window
        document.addEventListener('mouseleave', () => {
            cursorDot.style.opacity = '0';
            cursorOutline.style.opacity = '0';
        });
        
        document.addEventListener('mouseenter', () => {
            cursorDot.style.opacity = '1';
            cursorOutline.style.opacity = '1';
        });
    }
})();
