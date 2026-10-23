import os
import sys
import webview
from api import ApiBridge

def main():
    # Configure the API bridge
    api = ApiBridge()
    
    # Path to the compiled UI files
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    ui_dir = os.path.join(base_dir, 'ui')
    index_html = os.path.join(ui_dir, 'index.html')
    
    if not os.path.exists(index_html):
        print(f"Error: {index_html} not found. Please ensure the 'ui' folder exists.")
        url = None
    else:
        url = index_html

    # Path to the icon
    icon_path = os.path.join(base_dir, 'icon.ico')
    
    # Create the window
    window = webview.create_window(
        'File Sense',
        url=url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(800, 600),
        text_select=False,
        frameless=False,
        easy_drag=False,
        background_color='#0f172a'
    )
    
    api.set_window(window)
    
    # Start the webview application
    webview.start(
        debug=False,
        icon=icon_path if os.path.exists(icon_path) else None
    )

if __name__ == '__main__':
    main()
