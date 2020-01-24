depends on https://github.com/eckschi/libelperiodic

Lib ElPeriodic has 2 parts, one written in C and one in python

To build the packges on el7 use the software colletion:
```bash
sudo yum install centos-release-scl
sudo yum-config-manager --enable rhel-server-rhscl-7-rpms
sudo yum install devtoolset-8
scl enable devtoolset-8 bash
```
To build the RPM
```bash
./build_rpm.sh
```

To build the pip package
```bash
python3.4 setup.py bdist_wheel
```