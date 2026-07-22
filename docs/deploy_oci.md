# Deploy en Oracle Cloud (OCI Compute)

Guía paso a paso para publicar el agente en una máquina virtual gratuita de OCI (capa Always Free).

## 1. Crear la instancia

1. Entra a [cloud.oracle.com](https://cloud.oracle.com) y crea una cuenta (la capa Always Free no tiene costo).
2. Ve a **Compute → Instances → Create Instance**.
3. Configura:
   - **Image**: Ubuntu 22.04 (Canonical Ubuntu).
   - **Shape**: `VM.Standard.E2.1.Micro` (Always Free) o `VM.Standard.A1.Flex` (ARM, también gratis y con más RAM — recomendado).
   - **SSH keys**: descarga y guarda la clave privada (`.key`).
4. Crea la instancia y anota la **IP pública**.

## 2. Abrir el puerto 8501

Streamlit usa el puerto 8501. Hay que abrirlo en dos lugares:

**a) En la Security List de OCI:**
1. Ve a **Networking → Virtual Cloud Networks → Ingresa en el nombre de tu VCN → Ingresa directo al nombre de Default Route Table → Ingresa a la pestaña Route Rules**.
2. **Add Ingress Rule**: Source CIDR `0.0.0.0/0`, IP Protocol `TCP`, Destination Port Range `8501`.

**b) En el firewall de la VM (después de conectarte por SSH):**

⚠️ **Importante — el orden de las reglas importa.** La imagen de Ubuntu en OCI trae una regla `REJECT` que rechaza todo el tráfico. iptables evalúa las reglas de arriba hacia abajo y se detiene en la primera que coincide, así que si tu regla del 8501 queda *después* del REJECT, el puerto seguirá bloqueado aunque la regla exista.

Primero revisa dónde está el REJECT:
```bash
sudo iptables -L INPUT -n --line-numbers | grep -E "8501|REJECT"
```
 
Inserta la regla del 8501 **antes** del REJECT. Si el REJECT está en la línea 5, usa:
```bash
sudo iptables -I INPUT 5 -p tcp --dport 8501 -j ACCEPT
sudo netfilter-persistent save
```
 
Verifica que el `ACCEPT` del 8501 tenga un número de línea **menor** que el `REJECT`:
```bash
sudo iptables -L INPUT -n --line-numbers | grep -E "8501|REJECT"
```
 
> Si `netfilter-persistent` no existe: `sudo apt install -y iptables-persistent`.


## 3. Conectarse e instalar el proyecto

```bash
# Desde tu computadora
ssh -i ruta/a/tu_clave.key ubuntu@IP_PUBLICA

# Dentro de la VM
sudo apt update && sudo apt install -y python3-pip python3-venv git
git clone https://github.com/Marcoherna/bimbam-agente.git
cd bimbam-agente
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
La instalación tarda varios minutos (FAISS y LangChain son pesados). Ten paciencia.

## 4. Configurar la API key

El proyecto carga la clave desde un archivo `.env` (con `python-dotenv`). Créalo dentro de la VM:
 
```bash
cd ~/bimbam-agente
nano .env
```
 
Escribe una sola línea y guarda (`Ctrl+O`, Enter, `Ctrl+X`):
```
GOOGLE_API_KEY=tu_clave_de_gemini
```


## 5. Ejecutar la aplicación

```bash
# Prueba rápida (se cierra al salir de SSH)
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```
Abre http://IP_PUBLICA:8501 (con http, no https) y verifica que responde. Cuando confirmes que funciona, detén la prueba con Ctrl+C y configúrala como servicio permanente (paso 6).
## 6. Dejarla corriendo permanentemente (systemd)
 
Con `Ctrl+C` o al cerrar SSH la app se cae. Para que arranque sola y sobreviva reinicios, crea un servicio:
 
```bash
sudo nano /etc/systemd/system/agente.service
```
 
Pega esto (ajusta rutas si es necesario):
```ini
[Unit]
Description=Agente BimBam Buy
After=network.target
 
[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/bimbam-agente
ExecStart=/home/ubuntu/bimbam-agente/.venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
Restart=always
 
[Install]
WantedBy=multi-user.target
```
 
> Como la clave se lee desde `.env`, no hace falta la línea `Environment=`. Si prefieres pasarla aquí, agrega: `Environment="GOOGLE_API_KEY=tu_clave"`.
 
Activa el servicio (detén antes cualquier instancia manual que ocupe el puerto):
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now agente
sudo systemctl status agente     # debe decir "active (running)"
```
## Problemas frecuentes
 
| Síntoma | Solución |
|---|---|
| "No se puede conectar" / la página no carga | Revisa que el `ACCEPT` del 8501 esté **antes** del `REJECT` en iptables (paso 2b) y que la Ingress Rule de OCI exista (paso 2a). |
| `Port 8501 is not available` | Ya hay una instancia corriendo en ese puerto. No relances; usa la existente o deténla antes de arrancar el servicio. |
| `Killed` al instalar faiss | Usa la shape A1.Flex, o agrega swap: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile && echo '/swapfile none swap sw 0 0' \| sudo tee -a /etc/fstab`. |
| Error 404 de modelo | Usa modelos vigentes: `gemini-embedding-001` para embeddings y `gemini-2.5-flash` para generación. |
| Error de API key | Verifica que el archivo `.env` exista dentro de `~/bimbam-agente` con la línea `GOOGLE_API_KEY=...`. |
