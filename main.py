import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from datetime import datetime
import uuid
from config_manager import ConfigManager
from automation import ZoomAutomation

class ZoomAutoJoinGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Zoom Auto-Join System")
        self.root.geometry("1000x700")
        self.root.minsize(900, 650)
        
        self.config = ConfigManager()
        self.automation = None
        self.selected_user_id = None
        self.temp_user = None
        self.is_dark_mode = self.config.get_theme() == "dark"
        
        # Colors
        self.colors = {
            'dark': {
                'bg': '#0f0f1e',
                'secondary_bg': '#1a1a2e',
                'card_bg': '#16213e',
                'accent': '#00d4ff',
                'success': '#00ff88',
                'warning': '#ffd700',
                'error': '#ff4757',
                'text': '#e4e4e4',
                'text_secondary': '#a0a0a0'
            },
            'light': {
                'bg': '#f0f4f8',
                'secondary_bg': '#ffffff',
                'card_bg': '#ffffff',
                'accent': '#0066cc',
                'success': '#28a745',
                'warning': '#ff9800',
                'error': '#dc3545',
                'text': '#2d3748',
                'text_secondary': '#718096'
            }
        }
        
        self.apply_theme()
        self.show_start_screen()
        
    def apply_theme(self):
        theme = 'dark' if self.is_dark_mode else 'light'
        self.current_colors = self.colors[theme]
        self.root.configure(bg=self.current_colors['bg'])
        
    def toggle_theme(self):
        self.is_dark_mode = not self.is_dark_mode
        self.config.set_theme('dark' if self.is_dark_mode else 'light')
        self.apply_theme()
        # Refresh current screen
        if hasattr(self, 'automation_running') and self.automation_running:
            self.show_automation_screen()
        else:
            self.show_start_screen()
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_start_screen(self):
        self.clear_window()
        self.automation_running = False
        
        # Top bar
        top_bar = tk.Frame(self.root, bg=self.current_colors['secondary_bg'], height=60)
        top_bar.pack(fill='x', padx=0, pady=0)
        top_bar.pack_propagate(False)
        
        title_label = tk.Label(
            top_bar, 
            text="🎓 Zoom Auto-Join System", 
            font=('Helvetica', 18, 'bold'),
            bg=self.current_colors['secondary_bg'],
            fg=self.current_colors['accent']
        )
        title_label.pack(side='left', padx=20, pady=15)
        
        # Current time
        self.time_label = tk.Label(
            top_bar,
            text=datetime.now().strftime("%I:%M %p"),
            font=('Helvetica', 12),
            bg=self.current_colors['secondary_bg'],
            fg=self.current_colors['text']
        )
        self.time_label.pack(side='right', padx=20)
        self.update_time()
        
        # Theme toggle
        theme_btn = tk.Button(
            top_bar,
            text="🌙" if not self.is_dark_mode else "☀️",
            font=('Helvetica', 16),
            bg=self.current_colors['card_bg'],
            fg=self.current_colors['text'],
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.toggle_theme
        )
        theme_btn.pack(side='right', padx=10)
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.current_colors['bg'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Users
        left_panel = tk.Frame(content_frame, bg=self.current_colors['card_bg'], relief='flat', bd=2)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        users_header = tk.Label(
            left_panel,
            text="👥 Saved Users",
            font=('Helvetica', 14, 'bold'),
            bg=self.current_colors['card_bg'],
            fg=self.current_colors['text'],
            anchor='w'
        )
        users_header.pack(fill='x', padx=15, pady=(15, 10))
        
        # User list
        self.user_list_frame = tk.Frame(left_panel, bg=self.current_colors['card_bg'])
        self.user_list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        self.refresh_user_list()
        
        # Right panel - Actions & Cached Classes
        right_panel = tk.Frame(content_frame, bg=self.current_colors['card_bg'], relief='flat', bd=2)
        right_panel.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Selected user info
        info_header = tk.Label(
            right_panel,
            text="⚡ Quick Actions",
            font=('Helvetica', 14, 'bold'),
            bg=self.current_colors['card_bg'],
            fg=self.current_colors['text'],
            anchor='w'
        )
        info_header.pack(fill='x', padx=15, pady=(15, 10))
        
        # Start button
        self.start_btn = tk.Button(
            right_panel,
            text="▶ START ZOOM CLASS JOIN",
            font=('Helvetica', 14, 'bold'),
            bg=self.current_colors['success'],
            fg='white',
            bd=0,
            padx=20,
            pady=15,
            cursor='hand2',
            command=self.start_automation
        )
        self.start_btn.pack(fill='x', padx=15, pady=10)
        
        # Add user button
        add_btn = tk.Button(
            right_panel,
            text="➕ Add New User",
            font=('Helvetica', 12),
            bg=self.current_colors['accent'],
            fg='white',
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2',
            command=self.show_add_user_dialog
        )
        add_btn.pack(fill='x', padx=15, pady=5)
        
        # Edit button
        self.edit_btn = tk.Button(
            right_panel,
            text="✏️ Edit Selected",
            font=('Helvetica', 12),
            bg=self.current_colors['warning'],
            fg='white',
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2',
            command=self.edit_selected_user,
            state='disabled'
        )
        self.edit_btn.pack(fill='x', padx=15, pady=5)
        
        # Delete button
        self.delete_btn = tk.Button(
            right_panel,
            text="🗑️ Delete Selected",
            font=('Helvetica', 12),
            bg=self.current_colors['error'],
            fg='white',
            bd=0,
            padx=20,
            pady=12,
            cursor='hand2',
            command=self.delete_selected_user,
            state='disabled'
        )
        self.delete_btn.pack(fill='x', padx=15, pady=5)
        
        # Cached classes section
        cache_header = tk.Label(
            right_panel,
            text="🕐 Cached Classes (Today)",
            font=('Helvetica', 12, 'bold'),
            bg=self.current_colors['card_bg'],
            fg=self.current_colors['text'],
            anchor='w'
        )
        cache_header.pack(fill='x', padx=15, pady=(20, 10))
        
        self.cached_frame = tk.Frame(right_panel, bg=self.current_colors['card_bg'])
        self.cached_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        self.refresh_cached_classes()
    
    def refresh_user_list(self):
        for widget in self.user_list_frame.winfo_children():
            widget.destroy()
        
        users = self.config.get_all_users()
        
        if not users:
            no_user_label = tk.Label(
                self.user_list_frame,
                text="No saved users.\nClick 'Add New User' to get started!",
                font=('Helvetica', 11),
                bg=self.current_colors['card_bg'],
                fg=self.current_colors['text_secondary'],
                justify='center'
            )
            no_user_label.pack(expand=True)
            return
        
        self.user_var = tk.StringVar()
        
        for user in users:
            user_card = tk.Frame(
                self.user_list_frame,
                bg=self.current_colors['secondary_bg'],
                relief='flat',
                bd=1
            )
            user_card.pack(fill='x', pady=5)
            
            radio = tk.Radiobutton(
                user_card,
                variable=self.user_var,
                value=user['id'],
                bg=self.current_colors['secondary_bg'],
                fg=self.current_colors['text'],
                selectcolor=self.current_colors['card_bg'],
                activebackground=self.current_colors['secondary_bg'],
                command=self.on_user_selected
            )
            radio.pack(side='left', padx=10)
            
            info_frame = tk.Frame(user_card, bg=self.current_colors['secondary_bg'])
            info_frame.pack(side='left', fill='both', expand=True, padx=5, pady=8)
            
            name_label = tk.Label(
                info_frame,
                text=f"{user['first_name']} {user['last_name']}",
                font=('Helvetica', 11, 'bold'),
                bg=self.current_colors['secondary_bg'],
                fg=self.current_colors['text'],
                anchor='w'
            )
            name_label.pack(anchor='w')
            
            email_label = tk.Label(
                info_frame,
                text=f"📧 {user['email']}",
                font=('Helvetica', 9),
                bg=self.current_colors['secondary_bg'],
                fg=self.current_colors['text_secondary'],
                anchor='w'
            )
            email_label.pack(anchor='w')
    
    def on_user_selected(self):
        self.selected_user_id = self.user_var.get()
        self.edit_btn.config(state='normal')
        self.delete_btn.config(state='normal')
        self.start_btn.config(state='normal')
    
    def refresh_cached_classes(self):
        for widget in self.cached_frame.winfo_children():
            widget.destroy()
        
        cached = self.config.get_valid_cached_classes()
        
        if not cached:
            no_cache_label = tk.Label(
                self.cached_frame,
                text="No cached classes available",
                font=('Helvetica', 10),
                bg=self.current_colors['card_bg'],
                fg=self.current_colors['text_secondary']
            )
            no_cache_label.pack(pady=10)
            return
        
        for cls in cached:
            cache_card = tk.Frame(
                self.cached_frame,
                bg=self.current_colors['secondary_bg'],
                relief='flat',
                bd=1
            )
            cache_card.pack(fill='x', pady=5)
            
            class_info = tk.Label(
                cache_card,
                text=f"{cls['class_name']}\n⏰ {cls['class_time']}",
                font=('Helvetica', 9),
                bg=self.current_colors['secondary_bg'],
                fg=self.current_colors['text'],
                anchor='w',
                justify='left'
            )
            class_info.pack(side='left', padx=10, pady=8)
            
            rejoin_btn = tk.Button(
                cache_card,
                text="↻ Rejoin",
                font=('Helvetica', 9, 'bold'),
                bg=self.current_colors['accent'],
                fg='white',
                bd=0,
                padx=15,
                pady=5,
                cursor='hand2',
                command=lambda link=cls['zoom_link']: self.rejoin_class(link)
            )
            rejoin_btn.pack(side='right', padx=10)
    
    def rejoin_class(self, link):
        import webbrowser
        webbrowser.open(link)
        self.log_to_console(f"✓ Opened cached class link in browser", 'success')
    
    def update_time(self):
        if hasattr(self, 'time_label') and self.time_label.winfo_exists():
            current_time = datetime.now().strftime("%I:%M %p")
            self.time_label.config(text=current_time)
            self.root.after(1000, self.update_time)
    
    def show_add_user_dialog(self, edit_user=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New User" if not edit_user else "Edit User")
        dialog.geometry("500x650")
        dialog.configure(bg=self.current_colors['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header = tk.Label(
            dialog,
            text="➕ Add New User" if not edit_user else "✏️ Edit User",
            font=('Helvetica', 16, 'bold'),
            bg=self.current_colors['secondary_bg'],
            fg=self.current_colors['accent'],
            pady=15
        )
        header.pack(fill='x')
        
        # Form frame
        form_frame = tk.Frame(dialog, bg=self.current_colors['bg'])
        form_frame.pack(fill='both', expand=True, padx=30, pady=20)
        
        fields = {}
        
        # Site URL with dropdown
        tk.Label(form_frame, text="Site URL:", font=('Helvetica', 10, 'bold'),
                bg=self.current_colors['bg'], fg=self.current_colors['text']).pack(anchor='w', pady=(10, 2))
        
        site_urls = self.config.get_site_urls()
        fields['site_url'] = ttk.Combobox(form_frame, values=site_urls, font=('Helvetica', 10))
        fields['site_url'].pack(fill='x', pady=(0, 10))
        
        # Other fields
        field_labels = [
            ('username', 'Username'),
            ('password', 'Password'),
            ('first_name', 'First Name'),
            ('last_name', 'Last Name'),
            ('email', 'Email'),
            ('nic_number', 'NIC Number'),
            ('contact_number', 'Contact Number')
        ]
        
        for field_key, field_label in field_labels:
            tk.Label(form_frame, text=f"{field_label}:", font=('Helvetica', 10, 'bold'),
                    bg=self.current_colors['bg'], fg=self.current_colors['text']).pack(anchor='w', pady=(10, 2))
            
            if field_key == 'password':
                fields[field_key] = tk.Entry(form_frame, font=('Helvetica', 10), show='*')
            else:
                fields[field_key] = tk.Entry(form_frame, font=('Helvetica', 10))
            fields[field_key].pack(fill='x', pady=(0, 10))
        
        # Remember me checkbox
        remember_var = tk.BooleanVar(value=True if not edit_user else True)
        remember_check = tk.Checkbutton(
            form_frame,
            text="💾 Remember Me (Save credentials)",
            variable=remember_var,
            font=('Helvetica', 10),
            bg=self.current_colors['bg'],
            fg=self.current_colors['text'],
            selectcolor=self.current_colors['card_bg'],
            activebackground=self.current_colors['bg']
        )
        remember_check.pack(anchor='w', pady=10)
        
        # Pre-fill if editing
        if edit_user:
            fields['site_url'].set(edit_user['site_url'])
            fields['username'].insert(0, edit_user['username'])
            fields['password'].insert(0, self.config.decrypt_password(edit_user['password']))
            fields['first_name'].insert(0, edit_user['first_name'])
            fields['last_name'].insert(0, edit_user['last_name'])
            fields['email'].insert(0, edit_user['email'])
            fields['nic_number'].insert(0, edit_user['nic_number'])
            fields['contact_number'].insert(0, edit_user['contact_number'])
        
        # Buttons
        btn_frame = tk.Frame(form_frame, bg=self.current_colors['bg'])
        btn_frame.pack(fill='x', pady=20)
        
        def save_user():
            user_data = {key: field.get() for key, field in fields.items()}
            
            # Validation
            if not all(user_data.values()):
                messagebox.showerror("Error", "All fields are required!")
                return
            
            if remember_var.get():
                if edit_user:
                    user_data['id'] = edit_user['id']
                    self.config.update_user(user_data)
                else:
                    user_data['id'] = str(uuid.uuid4())
                    self.config.add_user(user_data)
                messagebox.showinfo("Success", "User saved successfully!")
            else:
                # Store temporarily for one-time use
                user_data['id'] = 'temp_' + str(uuid.uuid4())
                self.temp_user = user_data
                messagebox.showinfo("Success", "User loaded for one-time use!")
            
            dialog.destroy()
            self.show_start_screen()
        
        save_btn = tk.Button(
            btn_frame,
            text="💾 Save",
            font=('Helvetica', 12, 'bold'),
            bg=self.current_colors['success'],
            fg='white',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            command=save_user
        )
        save_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        
        cancel_btn = tk.Button(
            btn_frame,
            text="❌ Cancel",
            font=('Helvetica', 12, 'bold'),
            bg=self.current_colors['error'],
            fg='white',
            bd=0,
            padx=30,
            pady=10,
            cursor='hand2',
            command=dialog.destroy
        )
        cancel_btn.pack(side='right', expand=True, fill='x', padx=(5, 0))
    
    def edit_selected_user(self):
        if not self.selected_user_id:
            return
        user = self.config.get_user(self.selected_user_id)
        if user:
            self.show_add_user_dialog(edit_user=user)
    
    def delete_selected_user(self):
        if not self.selected_user_id:
            return
        
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?"):
            self.config.delete_user(self.selected_user_id)
            messagebox.showinfo("Success", "User deleted successfully!")
            self.show_start_screen()
    
    def start_automation(self):
        if not self.selected_user_id:
            messagebox.showwarning("Warning", "Please select a user first!")
            return
        
        user = self.config.get_user(self.selected_user_id)
        if not user:
            messagebox.showerror("Error", "User not found!")
            return
        
        self.current_user = user
        self.show_automation_screen()
        
        # Start automation in thread
        thread = threading.Thread(target=self.run_automation, daemon=True)
        thread.start()
    
    def show_automation_screen(self):
        self.clear_window()
        self.automation_running = True
        
        # Top bar
        top_bar = tk.Frame(self.root, bg=self.current_colors['secondary_bg'], height=60)
        top_bar.pack(fill='x', padx=0, pady=0)
        top_bar.pack_propagate(False)
        
        user_label = tk.Label(
            top_bar,
            text=f"👤 {self.current_user['first_name']} {self.current_user['last_name']}",
            font=('Helvetica', 16, 'bold'),
            bg=self.current_colors['secondary_bg'],
            fg=self.current_colors['accent']
        )
        user_label.pack(side='left', padx=20, pady=15)
        
        # Status indicator
        self.status_label = tk.Label(
            top_bar,
            text="⏳ Initializing...",
            font=('Helvetica', 11),
            bg=self.current_colors['secondary_bg'],
            fg=self.current_colors['warning']
        )
        self.status_label.pack(side='left', padx=10)
        
        # Time
        self.time_label = tk.Label(
            top_bar,
            text=datetime.now().strftime("%I:%M %p"),
            font=('Helvetica', 12),
            bg=self.current_colors['secondary_bg'],
            fg=self.current_colors['text']
        )
        self.time_label.pack(side='right', padx=20)
        self.update_time()
        
        # Theme toggle
        theme_btn = tk.Button(
            top_bar,
            text="🌙" if not self.is_dark_mode else "☀️",
            font=('Helvetica', 16),
            bg=self.current_colors['card_bg'],
            fg=self.current_colors['text'],
            bd=0,
            padx=15,
            pady=5,
            cursor='hand2',
            command=self.toggle_theme
        )
        theme_btn.pack(side='right', padx=10)
        
        # Main content
        content_frame = tk.Frame(self.root, bg=self.current_colors['bg'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Console output
        console_label = tk.Label(
            content_frame,
            text="📋 Console Output",
            font=('Helvetica', 12, 'bold'),
            bg=self.current_colors['bg'],
            fg=self.current_colors['text'],
            anchor='w'
        )
        console_label.pack(fill='x', pady=(0, 10))
        
        self.console = scrolledtext.ScrolledText(
            content_frame,
            font=('Courier', 10),
            bg=self.current_colors['card_bg'],
            fg=self.current_colors['text'],
            height=20,
            wrap='word',
            state='disabled'
        )
        self.console.pack(fill='both', expand=True)
        
        # Configure tags for colored output
        self.console.tag_config('success', foreground=self.current_colors['success'])
        self.console.tag_config('error', foreground=self.current_colors['error'])
        self.console.tag_config('warning', foreground=self.current_colors['warning'])
        self.console.tag_config('info', foreground=self.current_colors['accent'])
        
        # Buttons
        btn_frame = tk.Frame(content_frame, bg=self.current_colors['bg'])
        btn_frame.pack(fill='x', pady=(10, 0))
        
        self.stop_btn = tk.Button(
            btn_frame,
            text="⏹ STOP & GO BACK",
            font=('Helvetica', 12, 'bold'),
            bg=self.current_colors['error'],
            fg='white',
            bd=0,
            padx=30,
            pady=12,
            cursor='hand2',
            command=self.stop_automation
        )
        self.stop_btn.pack(side='left', expand=True, fill='x')
    
    def log_to_console(self, message, level='info'):
        if not hasattr(self, 'console') or not self.console.winfo_exists():
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}\n"
        
        self.console.config(state='normal')
        self.console.insert('end', formatted_msg, level)
        self.console.see('end')
        self.console.config(state='disabled')
    
    def update_status(self, status, level='info'):
        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            colors = {
                'success': self.current_colors['success'],
                'error': self.current_colors['error'],
                'warning': self.current_colors['warning'],
                'info': self.current_colors['accent']
            }
            self.status_label.config(text=status, fg=colors.get(level, self.current_colors['text']))
    
    def run_automation(self):
        try:
            self.log_to_console("🚀 Starting automation...", 'info')
            self.update_status("⏳ Logging in...", 'info')
            
            self.automation = ZoomAutomation(self.current_user, self.log_to_console, self.update_status)
            self.automation.run()
            
            # Cache the zoom link if available
            if hasattr(self.automation, 'zoom_link') and self.automation.zoom_link:
                self.config.cache_class({
                    'user_id': self.current_user['id'],
                    'class_name': self.automation.class_name or "Zoom Class",
                    'class_time': self.automation.class_time or "Time TBD",
                    'zoom_link': self.automation.zoom_link
                })
                self.log_to_console("💾 Class link cached for 24 hours", 'success')
            
            self.log_to_console("✅ Automation completed! Browser will remain open.", 'success')
            self.update_status("✅ Completed - Check Browser", 'success')
            
        except Exception as e:
            self.log_to_console(f"❌ Error: {str(e)}", 'error')
            self.update_status("❌ Error occurred", 'error')
    
    def stop_automation(self):
        if self.automation:
            self.automation.stop()
        self.show_start_screen()

def main():
    root = tk.Tk()
    app = ZoomAutoJoinGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()