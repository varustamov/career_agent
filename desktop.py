"""Desktop launcher for the local dashboard."""
import os
import sys
import threading
import webbrowser
from http.server import ThreadingHTTPServer
from pathlib import Path


def data_dir():
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'Career Agent'
    if sys.platform == 'win32':
        return Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Career Agent'
    return Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local' / 'share'))) / 'career-agent'


def main():
    import tkinter as tk
    from tkinter import messagebox

    database = Path(os.environ.get('CAREER_DB_PATH') or data_dir() / 'jobs.sqlite3')
    database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.environ['CAREER_DB_PATH'] = str(database)
    os.environ.setdefault('CAREER_PORT', '18766')
    # The dashboard reads its database path and port when it is imported.
    import dashboard_server as dashboard

    window = tk.Tk()
    window.title('Career Agent')
    window.resizable(False, False)
    try:
        server = ThreadingHTTPServer(('127.0.0.1', dashboard.PORT), dashboard.Handler)
    except OSError:
        messagebox.showerror('Career Agent', 'The local port is already in use. Close the other instance and try again.')
        window.destroy()
        return

    dashboard.scheduler.start()
    config = dashboard.ai_workflow.get_config()
    dashboard.ai_scheduler.configure(config['enabled'], config['interval_minutes'])
    dashboard.ai_scheduler.start()
    threading.Thread(target=server.serve_forever, daemon=True).start()

    url = f'http://127.0.0.1:{dashboard.PORT}/'
    frame = tk.Frame(window, padx=24, pady=22)
    frame.pack()
    tk.Label(frame, text='Career Agent', font=('Helvetica', 19, 'bold')).pack(anchor='w')
    tk.Label(
        frame,
        text='Your private job search is running on this device.\nKeep this window open while using the app.',
        justify='left',
    ).pack(anchor='w', pady=(10, 18))
    tk.Button(frame, text='Open dashboard', command=lambda: webbrowser.open(url)).pack(fill='x')

    def quit_app():
        server.shutdown()
        server.server_close()
        window.destroy()

    tk.Button(frame, text='Quit Career Agent', command=quit_app).pack(fill='x', pady=(8, 0))
    window.protocol('WM_DELETE_WINDOW', quit_app)
    if '--no-browser' not in sys.argv[1:]:
        window.after(400, lambda: webbrowser.open(url))
    window.mainloop()


if __name__ == '__main__':
    main()
