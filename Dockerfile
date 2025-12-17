FROM python:3.10-slim

# Définir des variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LOG_LEVEL=INFO

# Créer et définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances et installer les dépendances
COPY requirements.txt .
COPY pyproject.toml .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir -r requirements.txt

# Copier le reste du code
COPY src ./src
COPY . .

# Installez le paquet pour que Python puisse trouver le module mcp_server_grist
RUN pip install -e .

# Exposer les ports pour les modes HTTP
EXPOSE 3000

# Définir les variables d'environnement pour la configuration de Grist
ENV GRIST_API_KEY=""
ENV GRIST_API_HOST="https://grist.numerique.gouv.fr/api"

# Utilisez par défaut streamable-http pour le déploiement dans le cloud
CMD ["python", "-m", "mcp_server_grist", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "3000", "--path", "/mcp"]

# Exemples d'utilisation du conteneur:
# Mode stdio (par défaut):
#   docker run --rm -i -e GRIST_API_KEY=your_key mcp/grist-mcp-server
# 
# Mode streamable-http:
#   docker run --rm -p 8000:8000 -e GRIST_API_KEY=your_key mcp/grist-mcp-server --transport streamable-http
#
# Mode SSE:
#   docker run --rm -p 8000:8000 -e GRIST_API_KEY=your_key mcp/grist-mcp-server --transport sse
