from fileinput import FileInput

with open('/etc/nginx/nginx.conf') as oldfile:
    for line in oldfile:
        if "var/log" in line:
            line = line.replace('/var/log/nginx/','syslog:server=unix:/dev/')
            line = line.replace("access.","")
            line = line.replace("error.","")
        if "Logging Settings" in line:
            line+="        ##log to the systemd journal instead of to separate log files\n"
        print(line,end='')
        
