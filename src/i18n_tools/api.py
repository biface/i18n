import requests
import validators

def validate_api_url(url: str, timeout: int = 5) -> dict:
    """
    Valide un lien en vérifiant son format et sa disponibilité.

    :param url: L'URL à valider.
    :param timeout: Temps d'attente maximum pour la réponse du serveur (en secondes).
    :return: Un dictionnaire contenant le statut de validation et des détails sur l'URL.
    """
    result = {
        "url": url,
        "is_alive": False,
        "status_code": None,
        "error": None,
    }

    # Validation du format de l'URL
    if not validators.url(url):
        result["error"] = f"L'URL '{url}' n'est pas valide au format."
        return result

    # Vérification de l'accessibilité de l'URL
    try:
        response = requests.get(url, timeout=timeout)
        result["status_code"] = response.status_code

        # Vérifier si le serveur est vivant malgré des codes d'erreur spécifiques
        if response.status_code in {401, 403, 405, 429, 500}:
            result["is_alive"] = True  # Le serveur est vivant mais un accès correct nécessite des ajustements
        elif 200 <= response.status_code < 300:
            result["is_alive"] = True  # Le serveur est accessible et répond correctement
        else:
            result["error"] = f"Code de statut inattendu: {response.status_code}"
    except requests.exceptions.Timeout:
        result["error"] = "Le délai de connexion a expiré."
    except requests.exceptions.ConnectionError:
        result["error"] = "Impossible de se connecter au serveur."
    except requests.exceptions.RequestException as e:
        result["error"] = str(e)

    return result
