This requires < Python 3.11 to run.

Install the [Azure Function Tools](https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local?tabs=v4%2Clinux%2Ccsharp%2Cportal%2Cbash#local-settings-file)

```sh
curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg

# Debian/Codespace
sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/debian/$(lsb_release -rs | cut -d'.' -f 1)/prod $(lsb_release -cs) main" > /etc/apt/sources.list.d/dotnetdev.list'

sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

Create a new python env when testing the function.

```sh
python3.9 -m venv .venv/py39
source .venv/py39/bin/activate

python3.9 -m pip install flit
python3.9 -m flit install

cd azure/api
python 3.9
func start

```