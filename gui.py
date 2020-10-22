import os
import time
import tkinter
import tkinter.messagebox
import pickle

dirpath = os.path.dirname(__file__) + '/'

'''
VERSION: 
0.1.5 Under Development
'''

'''
KNOWN BUGS:
* Under macOS printing using print() crashes the program when running from the bash script
need to fix the bash script probably, removed prints for now.'''

'''
CHANGE LOG:
0.1.1 - Start, Stop, View (cmd)
0.1.2 - Added gui
0.1.3 - 
    1. Added auto-save of progress into an external file
    2. Auto load progress when reopening
0.1.4 -
    1. Added a pause button, allowing to pause a session and resume it later by pressing the start button
    2. Added a reset button, allowing to reset the total time displayed (full history is still being saved)
    3. Added git repository to github: https://github.com/avnerduc/TimeMachine.git
0.1.5 - 
    1. Resetting a session when it's running or paused will now stop the session and save it before resetting timer
    2. Added git repository to BitBucket: https://avnerduc@bitbucket.org/avnerduc/timemachine.git
    3. Code adjustments, added basic documentation
    4. The timer is now always on top
    5. The timer now has a constant title - 'TM'
    6. Added interpreter-dependant scripts that run the timer for Windows and for Mac
    7. Gui width increased so it is draggable, starting gui width is dependant on title
'''

'''
Ideas for further versions:
* Add exception (Single type)
* Code update: clean up gui construction
* Add a drop down menu to allow user to choose a category for his session
* make an executable file for the project
* Make moving the window easier (not require right click)
* always on top toggle
* Abort session (a button when clicked discards the last part of the session, from start or from last pause)
* Add an option to cancel current session (button) (duplicate?)
* Show time since last session
* Running / Not running color indication
* Add an indicator of the current status (duplicate?)
* smart login - user can put username and continue. you can give a password, but don't have to
* Upon pausing a session - rename Start button to Resume (merge the two buttons)
* Add an option to create new categories
* Allow continuing from a closed running or paused session
* When resetting, verify with user (confirmation window)

Completed ideas that didn't make it to the changelog:
* Add a method to which you give time by epoch and it translates it into a string (0.1.5)

Postponed ideas:
* Render irrelevant buttons un-clickable when relevant
'''


def format_time(ticks):
    return time.strftime('%H:%M:%S', time.gmtime(ticks))


class SessionMaster:
    PROG_TITLE = "TM"
    INFO = "This is a Time Machine.\n" \
           "Remember: There is no going back in time."
    GUI_REFRESH_RATE = 10  # in milliseconds

    def __init__(self):
        self.history = []
        self.last_reset = 0
        self.curr_sess = None
        self.load()
        self.root_tk = tkinter.Tk()
        self.root_tk.title(SessionMaster.PROG_TITLE)

        self.info = tkinter.Button(self.root_tk, text="Info", command=self.display_info)
        self.info.pack()
        self.session_time = tkinter.Label()
        self.session_time.pack()
        self.set_session_timer(0)
        self.total_time = tkinter.Label()
        self.total_time.pack()
        self.set_total_timer(0)
        self.start_bot = tkinter.Button(self.root_tk, text="Start", command=self.start)
        self.start_bot.pack()
        self.pause_bot = tkinter.Button(self.root_tk, text="Pause", command=self.pause)
        self.pause_bot.pack()
        self.stop_bot = tkinter.Button(self.root_tk, text="Stop", command=self.stop)
        self.stop_bot.pack()
        self.reset_bot = tkinter.Button(self.root_tk, text="Reset", command=self.reset)
        self.reset_bot.pack()
        # Added
        self.root_tk.update()
        size = str(self.root_tk.winfo_width()+37+(len(SessionMaster.PROG_TITLE)*7))+"x"+str(self.root_tk.winfo_height())
        self.root_tk.geometry(size)
        self.root_tk.attributes('-topmost', True)
        try:
            with open(dirpath + "geo.pickle", 'rb') as geometry_handle:
                self.root_tk.geometry(pickle.load(geometry_handle))
        except IOError:
            pass
        #self.root_tk.minsize(width=self.root_tk.winfo_width(), height=self.root_tk.winfo_height())
        # deddA
        self.refresh()
        #self.root_tk.mainloop()

    '''on window close event: saving session and window geometry and closing TM'''
    def client_exit(self):
        # no session running
        if not self.curr_sess or not self.curr_sess.get_status():
            self.save_geometry()
        else:  # session running, saving time and geometry
            self.stop_running_session()
        self.root_tk.destroy()
        return True


    '''Loads progress from file: Loads full session history of the user, as well as the last reset time.'''
    def load(self):
        try:
            with open(dirpath + "history.pickle", 'rb') as history_handle:
                self.history = pickle.load(history_handle)
        except IOError:
            # print("No saved progress found")
            pass
        try:
            with open(dirpath + "reset.pickle", 'rb') as reset_handle:
                self.last_reset = pickle.load(reset_handle)
        except IOError:
            pass  # This happens when no reset command was loaded. Legal and requires no action or feedback


    '''Saving window position and size'''
    def save_geometry(self):
        try:
            with open(dirpath + 'geo.pickle', 'wb') as geometry_handle:
                pickle.dump(self.root_tk.geometry(), geometry_handle, protocol=pickle.HIGHEST_PROTOCOL)
        except IOError:
            # print("Error while saving geometry")
            pass
        return True


    '''Saves the session history and the last reset time to external files'''
    def save(self):
        try:
            with open(dirpath + 'history.pickle', 'wb') as history_handle:
                pickle.dump(self.history, history_handle, protocol=pickle.HIGHEST_PROTOCOL)
            with open(dirpath + 'reset.pickle', 'wb') as reset_handle:
                pickle.dump(self.last_reset, reset_handle, protocol=pickle.HIGHEST_PROTOCOL)

        except IOError:
            # print("Error while saving progress")
            pass
        self.save_geometry()
        return True



    '''Start a session or resume a paused one'''
    def start(self):
        if self.curr_sess and self.curr_sess.get_status():
            if self.curr_sess.get_status() == SessionMaster.Session.PAUSED:
                self.curr_sess.start()
                self.refresh()
                # print("Resuming session")
                return True
            if self.curr_sess.get_status() == SessionMaster.Session.RUNNING:
                # print("You are already in a session")
                return False
        self.curr_sess = SessionMaster.Session(len(self.history) + 1)  # TODO if the master is indexing, remove argument
        self.curr_sess.start()
        self.refresh()
        # print("Session {0} Started".format(self.curr_sess.get_id()))

    '''Pause a currently running session'''
    def pause(self):
        if not self.curr_sess or not self.curr_sess.get_status():
            # print("There is no active session")
            return False
        if self.curr_sess.get_status() == SessionMaster.Session.PAUSED:
            # print("Session is already paused")
            return False
        self.curr_sess.pause()
        # print("Session Paused")
        return True

    '''Stop a currently running session'''
    def stop_running_session(self):
        self.curr_sess.stop()
        self.history.append(self.curr_sess)
        self.save()
        # print("Session {0} Stopped".format(self.curr_sess.get_id()))
        # print(self)  # Prints full history
        return True

    '''Stop a currently running or paused session'''
    def stop(self):
        if not self.curr_sess or not self.curr_sess.get_status():
            # print("There is no active session")
            return False
        return self.stop_running_session()

    '''Resets the total time timer.
    Preserves information regarding previous sessions.'''
    def reset(self):
        self.last_reset = time.time()
        if self.curr_sess and self.curr_sess.get_status():
            self.stop()
        self.save()
        self.set_total_timer(0)
        # print("Counter Reset")

    '''Updates the GUI, refreshing current session and total time.
    If there is a running session, will schedule another GUI refresh according to SessionMaster.GUI_REFRESH_RATE'''
    def refresh(self):
        self.set_total_timer(self.get_total())
        if self.curr_sess and self.curr_sess.get_status():
            self.set_session_timer(self.curr_sess.get_total())
            self.root_tk.after(SessionMaster.GUI_REFRESH_RATE, self.refresh)

    '''Updates the 'Current Session' display in the gui'''
    def set_session_timer(self, new_time):
        self.session_time.configure(text="Current session: " + format_time(new_time))

    '''Updates the 'Completed' display in the gui'''
    def set_total_timer(self, new_time):
        self.total_time.configure(text="Completed: " + format_time(new_time))

    '''Returns the sum of session time of all sessions since last reset'''
    def get_total(self):
        total = 0
        for sess in self.history:
            if sess.get_start_time() > self.last_reset:
                total += sess.get_total()
        if self.curr_sess and self.curr_sess.get_status():
            total += self.curr_sess.get_total()
        return total

    '''Displays an welcome message to the user'''
    @staticmethod
    def display_info():
        tkinter.messagebox.showinfo("Info", SessionMaster.INFO)

    '''Returns a string representation of the SessionMaster'''
    def __repr__(self):
        repr_str = "Here is your progress - Total time: {0}, Sessions: {1}, Session History:".\
            format(format_time(self.get_total()), len(self.history))
        for sess in self.history:
            repr_str += "\n"+sess.__repr__()
        return repr_str

    '''Inner class of SessionMaster'''
    class Session:

        STOPPED = 0
        RUNNING = 1
        PAUSED = 2

        def __init__(self, sess_num, cat="default"):
            self.id = sess_num  # TODO remove this and let SessionMaster assign numbers to sessions?
            #  If SessionMaster saves a list of sessions, this is data duplication.
            self.category = cat
            self.status = SessionMaster.Session.STOPPED
            self.start_ticks = None
            self.total_ticks = 0

        def start(self):
            self.status = SessionMaster.Session.RUNNING
            self.start_ticks = time.time()

        def pause(self):
            self.status = SessionMaster.Session.PAUSED
            self.total_ticks += int(time.time() - self.start_ticks)

        def stop(self):
            if self.get_status() == SessionMaster.Session.RUNNING:
                self.total_ticks += int(time.time() - self.start_ticks)
            self.status = SessionMaster.Session.STOPPED

        def get_status(self):
            return self.status

        def get_total(self):
            if self.status == SessionMaster.Session.RUNNING:
                return self.total_ticks + (time.time() - self.start_ticks)
            return self.total_ticks

        def get_start_time(self):
            return self.start_ticks

        def get_id(self):
            return self.id

        def __repr__(self):
            return "Session #{0}: Cat: {1}, Start: {2}, Total: {3}"\
                .format(self.id, self.category, format_time(self.start_ticks), format_time(self.get_total()))


if __name__ == "__main__":
    session_master = SessionMaster()  # session_master.root_tk is root window
    # attach deletion handler to 'client_exit' method
    session_master.root_tk.protocol("WM_DELETE_WINDOW", session_master.client_exit)
    session_master.root_tk.mainloop()
