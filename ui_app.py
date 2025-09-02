import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
from systemgeneralsearch import search_part_number_in_system_general_limited
from dataiosearch import search_part_number_in_dataio
from bpmicrosearch import search_part_number_in_bpmicro


class DeviceSearchUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Device Search Application")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Variables for checkboxes
        self.system_general_var = tk.BooleanVar()
        self.dataio_var = tk.BooleanVar()
        self.bpmicro_var = tk.BooleanVar()
        
        # Variable for search entry
        self.search_var = tk.StringVar()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Device Search Application", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Search input section
        search_label = ttk.Label(main_frame, text="Part Number:")
        search_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.search_entry = ttk.Entry(main_frame, textvariable=self.search_var, 
                                     font=("Arial", 12), width=30)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Website selection section
        websites_label = ttk.Label(main_frame, text="Select Websites:")
        websites_label.grid(row=2, column=0, sticky=tk.W, pady=(20, 5))
        
        # Checkboxes frame
        checkbox_frame = ttk.Frame(main_frame)
        checkbox_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(20, 5), padx=(10, 0))
        
        self.system_general_cb = ttk.Checkbutton(checkbox_frame, text="System General", 
                                               variable=self.system_general_var)
        self.system_general_cb.grid(row=0, column=0, sticky=tk.W, padx=(0, 20))
        
        self.dataio_cb = ttk.Checkbutton(checkbox_frame, text="DataIO", 
                                        variable=self.dataio_var)
        self.dataio_cb.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.bpmicro_cb = ttk.Checkbutton(checkbox_frame, text="BPMicro", 
                                         variable=self.bpmicro_var)
        self.bpmicro_cb.grid(row=0, column=2, sticky=tk.W)
        
        # Search button
        self.search_button = ttk.Button(main_frame, text="Search", 
                                       command=self.start_search, style="Accent.TButton")
        self.search_button.grid(row=3, column=0, columnspan=2, pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=3, column=2, sticky=(tk.W, tk.E), pady=20, padx=(10, 0))
        
        # Results section
        results_label = ttk.Label(main_frame, text="Search Results:", 
                                 font=("Arial", 12, "bold"))
        results_label.grid(row=4, column=0, sticky=(tk.W, tk.N), pady=(0, 5))
        
        # Results text area with scrollbar
        self.results_text = scrolledtext.ScrolledText(main_frame, height=20, width=80, 
                                                     font=("Consolas", 10))
        self.results_text.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), 
                              pady=(25, 0))
        
        # Clear results button
        clear_button = ttk.Button(main_frame, text="Clear Results", 
                                 command=self.clear_results)
        clear_button.grid(row=5, column=0, pady=10, sticky=tk.W)
        
    def start_search(self):
        """Start the search in a separate thread to prevent UI freezing"""
        part_number = self.search_var.get().strip()
        
        if not part_number:
            messagebox.showerror("Error", "Please enter a part number")
            return
            
        # Check if at least one website is selected
        if not (self.system_general_var.get() or self.dataio_var.get() or self.bpmicro_var.get()):
            messagebox.showerror("Error", "Please select at least one website")
            return
        
        # Disable search button and start progress bar
        self.search_button.config(state='disabled')
        self.progress.start()
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        # Start search in separate thread
        search_thread = threading.Thread(target=self.perform_search, args=(part_number,))
        search_thread.daemon = True
        search_thread.start()
        
    def perform_search(self, part_number):
        """Perform the actual search operations"""
        try:
            self.append_result(f"Starting search for part number: {part_number}\n")
            self.append_result("=" * 60 + "\n\n")
            
            results_found = False
            
            # Search System General if selected
            if self.system_general_var.get():
                self.append_result("🔍 Searching System General...\n")
                try:
                    result = search_part_number_in_system_general_limited(part_number)
                    if result:
                        socket_info, actual_part = result
                        self.append_result(f"✅ System General: FOUND\n")
                        self.append_result(f"   Socket/SKB: {socket_info}\n")
                        self.append_result(f"   Part Number Used: {actual_part}\n")
                        if actual_part != part_number:
                            self.append_result(f"   ⚠️  Original part number modified (removed {len(part_number) - len(actual_part)} characters)\n")
                        self.append_result("\n")
                        results_found = True
                    else:
                        self.append_result(f"❌ System General: NOT FOUND\n\n")
                except Exception as e:
                    self.append_result(f"❌ System General: ERROR - {str(e)}\n\n")
            
            # Search DataIO if selected
            if self.dataio_var.get():
                self.append_result("🔍 Searching DataIO...\n")
                try:
                    result = search_part_number_in_dataio(part_number)
                    if result:
                        socket_info, actual_part = result
                        self.append_result(f"✅ DataIO: FOUND\n")
                        self.append_result(f"   Socket/Adapter: {socket_info}\n")
                        self.append_result(f"   Part Number Used: {actual_part}\n")
                        if actual_part != part_number:
                            self.append_result(f"   ⚠️  Original part number modified (removed {len(part_number) - len(actual_part)} characters)\n")
                        self.append_result("\n")
                        results_found = True
                    else:
                        self.append_result(f"❌ DataIO: NOT FOUND\n\n")
                except Exception as e:
                    self.append_result(f"❌ DataIO: ERROR - {str(e)}\n\n")
            
            # Search BPMicro if selected
            if self.bpmicro_var.get():
                self.append_result("🔍 Searching BPMicro...\n")
                try:
                    result = search_part_number_in_bpmicro(part_number)
                    if result:
                        socket_info, actual_part = result
                        self.append_result(f"✅ BPMicro: FOUND\n")
                        self.append_result(f"   Socket Number: {socket_info}\n")
                        self.append_result(f"   Part Number Used: {actual_part}\n")
                        if actual_part != part_number:
                            self.append_result(f"   ⚠️  Original part number modified (removed {len(part_number) - len(actual_part)} characters)\n")
                        self.append_result("\n")
                        results_found = True
                    else:
                        self.append_result(f"❌ BPMicro: NOT FOUND\n\n")
                except Exception as e:
                    self.append_result(f"❌ BPMicro: ERROR - {str(e)}\n\n")
            
            # Summary
            self.append_result("=" * 60 + "\n")
            if results_found:
                self.append_result("🎉 Search completed! Results found above.\n")
            else:
                self.append_result("😞 Search completed. No results found on any selected website.\n")
                
        except Exception as e:
            self.append_result(f"💥 Unexpected error: {str(e)}\n")
        finally:
            # Re-enable search button and stop progress bar
            self.root.after(0, self.search_complete)
    
    def append_result(self, text):
        """Safely append text to results area from any thread"""
        self.root.after(0, lambda: self._append_text(text))
    
    def _append_text(self, text):
        """Internal method to append text (must be called from main thread)"""
        self.results_text.insert(tk.END, text)
        self.results_text.see(tk.END)
        self.root.update_idletasks()
    
    def search_complete(self):
        """Called when search is complete to re-enable UI"""
        self.search_button.config(state='normal')
        self.progress.stop()
    
    def clear_results(self):
        """Clear the results text area"""
        self.results_text.delete(1.0, tk.END)


def main():
    root = tk.Tk()
    app = DeviceSearchUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
