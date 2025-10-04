from collections import deque
import os

status = [
	"INFO",
	"WARNING",
	"ERROR",
	"DEBUG",
]

class Logger:
	def __init__(self, parent):
		self.parent = parent
		# State management deque to track last log call for grouping
		self.state_history = deque(maxlen=1)  # Only need last state
		self.in_multi_group = False  # Track if we're in a multi-message group

	def _get_log_file_path(self):
		"""Get the full path to the log file and ensure directory exists"""
		if not hasattr(self.parent, 'Logdirectory') or not self.parent.Logdirectory:
			return None

		log_dir = self.parent.Logdirectory.eval() if hasattr(self.parent.Logdirectory, 'eval') else str(self.parent.Logdirectory)
		filename = f"{self.parent.Name}.log"
		full_path = os.path.join(log_dir, filename)

		# Ensure directory exists
		os.makedirs(log_dir, exist_ok=True)

		return full_path

	def _write_to_file(self, message, mode='a'):
		"""Write message to log file if Writetofile is enabled"""
		try:
			if not hasattr(self.parent, 'Writetofile') or not self.parent.Writetofile:
				return

			# Check if it's a toggle parameter (has eval method) or boolean
			write_enabled = self.parent.Writetofile.eval() if hasattr(self.parent.Writetofile, 'eval') else bool(self.parent.Writetofile)

			if not write_enabled:
				return

			file_path = self._get_log_file_path()
			if not file_path:
				return

			with open(file_path, mode, encoding='utf-8') as f:
				f.write(message + '\n')

		except (OSError, IOError, AttributeError) as e:
			# Silently fail on file operations - don't interrupt logging
			pass

	def _format_process(self, process):
		"""Handle process as string, list, or None"""
		if isinstance(process, list):
			# Filter out empty strings and join with colons
			return ':'.join(str(p) for p in process if p)
		return process if process else None

	def _build_prefix(self, status, process):
		"""Build the full prefix string"""
		display_status = status.upper()
		if process:
			return f"<{self.parent.Name} [{display_status}:{process}]>"
		else:
			return f"<{self.parent.Name} [{display_status}]>"

	def _should_show_full_prefix(self, current_state):
		"""Determine if we should show full prefix or continue group"""
		status, process, multi = current_state

		# Always show full prefix if multi=False
		if not multi:
			self.in_multi_group = False
			return True

		# Show full prefix if no previous state
		if not self.state_history:
			self.in_multi_group = True
			return True

		prev_status, prev_process, prev_multi = self.state_history[-1]

		# Status change always breaks group
		if prev_status != status:
			self.in_multi_group = True
			return True

		# Process change always breaks group (show full prefix)
		if prev_process != process:
			self.in_multi_group = True
			return True

		# Same status and process = continuation if in group
		if self.in_multi_group:
			return False

		# Start new group
		self.in_multi_group = True
		return True

	def __call__(self, msg=None, status='info', process=None, multi=True):
		if msg is None:
			msg = ''
		# Normalize process
		normalized_process = self._format_process(process)
		current_state = (status.upper(), normalized_process, multi)

		show_full_prefix = self._should_show_full_prefix(current_state)

		# Update history
		self.state_history.append(current_state)

		if show_full_prefix:
			# Full prefix for new groups or breaks
			prefix = self._build_prefix(status, normalized_process)
			log_message = f"{prefix} {msg}"
			print(log_message)
			self._write_to_file(log_message)
		else:
			# Continuation within same process group
			log_message = f" {msg}"
			print(log_message)
			self._write_to_file(log_message)

	def flush(self):
		"""Full reset of state and grouping"""
		self.state_history.clear()
		self.in_multi_group = False

		# Clear the log file if file writing is enabled
		try:
			if hasattr(self.parent, 'Writetofile'):
				write_enabled = self.parent.Writetofile.eval() if hasattr(self.parent.Writetofile, 'eval') else bool(self.parent.Writetofile)
				if write_enabled:
					file_path = self._get_log_file_path()
					if file_path:
						# Clear the file by opening in write mode
						with open(file_path, 'w', encoding='utf-8'):
							pass
		except (OSError, IOError, AttributeError):
			# Silently fail on file operations
			pass

		self(status='debug', process='Flush')

class root(Logger):
	def __init__(self, grandFatherComp):
		Logger.__init__(self, self) #  Inheritance pattern with bidirectional referencing magic
		self.grandFatherComp = grandFatherComp
		self.ownerComp = parent.OPLogger

		# Dynamically generate self.pars based off name
		for i in self.ownerComp.customPars:
			setattr(self, i.name.capitalize(), i)
