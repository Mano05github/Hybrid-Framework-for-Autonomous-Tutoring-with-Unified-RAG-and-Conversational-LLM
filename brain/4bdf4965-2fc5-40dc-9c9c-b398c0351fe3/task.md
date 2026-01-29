# SHG Member ID Card Photo Automation (Semi-Automated)

- [ ] Project Setup
    - [/] Create virtual environment and install dependencies (add `rembg`)
    - [ ] Update project structure (`main.py` cleanup)
- [x] Image Processing Module
    - [x] Implement Background Removal (White BG)
    - [x] Implement resizing/cropping (300x400px)
    - [x] Test with sample images (Implicit via main script)
- [x] Automation Script - Member Loop
    - [x] Implement `process_group` loop
    - [x] Implement `download_right_image`
    - [x] Implement `upload_image`
    - [x] Implement `go_back` navigation
- [ ] Verification
    - [ ] Run `test_image.py` (Local verification)
    - [ ] Run `main.py` against `mock_portal.html` (Safe flow verification)
    - [ ] Run `main.py` against Real Portal
