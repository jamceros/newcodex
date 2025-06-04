# Fichador Basico

Pequeña aplicación web para registrar usuarios y fichar inicio y fin de jornada laboral.

## Requisitos

- Python 3.8+
- Dependencias listadas en `requirements.txt`
- Una base de datos MySQL accesible

## Instalación

```bash
pip install -r requirements.txt
```

Configura las siguientes variables de entorno para conectar con tu base de datos MySQL:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=usuario
DB_PASSWORD=contraseña
DB_NAME=fichador
```

## Uso

```bash
python app.py
```

La aplicación arrancará en `http://localhost:5000`.

## Funcionalidades

- Registro de usuarios
- Inicio de sesión y cierre de sesión
- Fichar entrada y salida
- Listado de fichajes personales
