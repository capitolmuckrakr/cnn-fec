from fileinput import FileInput

with FileInput(files=['/home/ubuntu/scripts/cnn-fec/systemd/cnn-fec'], inplace=True) as oldfile:
    for line in oldfile:
        if "EC2IP" in line:
            myip=get_ipython().getoutput('curl -s -o- http://169.254.169.254/latest/meta-data/public-hostname/')
            myip="    server_name "+myip[0]
            print(myip)
        else:
            print(line,end='')
