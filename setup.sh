#!/bin/bash

# Create directories
mkdir -p /home/nirwog/CascadeProjects/Dark/static/images
mkdir -p /home/nirwog/CascadeProjects/Dark/static/css
mkdir -p /home/nirwog/CascadeProjects/Dark/static/js

# Copy SVG files
cat > /home/nirwog/CascadeProjects/Dark/static/images/dark-web-icon.svg << 'EOL'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"/>
  <line x1="12" y1="2" x2="12" y2="22"/>
  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
  <line x1="2" y1="12" x2="22" y2="12"/>
</svg>
EOL

cat > /home/nirwog/CascadeProjects/Dark/static/images/cyber-search.svg << 'EOL'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="11" cy="11" r="8"/>
  <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  <path d="M8 11h6"/>
  <path d="M11 8v6"/>
</svg>
EOL

# Run the Python script to generate images
cd /home/nirwog/CascadeProjects/Dark
python create_pattern.py

echo "Setup completed!"
