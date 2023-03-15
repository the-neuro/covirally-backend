import json
import logging
from dataclasses import dataclass
from typing import TypedDict

from httpx import TimeoutException

from app.config import settings, AppEnvTypes
from app.http_cli import http_client


logger = logging.getLogger(__name__)


DEFAULT_AVATAR_URL = "https://uploads-ssl.webflow.com/63b039a8224d1f6125175085/63b41a89196e1857c6be6b25_logo.svg"  # noqa


@dataclass
class SendMessageParams:
    """
    from_covirally_user: prefix before @. For example: noreply, ceo, mailgun.
        It then concatinates with domain. So, it will be noreply@<domain>.
    """

    from_covirally_user: str
    to_addresses: list[str] | str
    subject: str | None = None

    text: str | None = None
    html: str | None = None

    template: str | None = None
    template_variables: str | None = None

    domain: str | None = None

    def __post_init__(self) -> None:
        if all((self.html, self.text, self.template)):
            err = "Only one of 'html', 'text' or 'template' parameters must be set."
            raise ValueError(err)

        if not any((self.text, self.html, self.template)):
            raise ValueError("'Text', 'html' or 'template' parameter must be set")


class EmailConfirmationParams(TypedDict):
    avatar: str | None
    username: str | None
    email: str
    confirm_link: str


class ForgotPasswordParams(TypedDict):
    avatar: str | None
    username: str | None
    reset_link: str


class MailgunClient:
    def __init__(self, api_key: str | None, domain: str = "mail.covirally.com"):
        self.__api_key = api_key
        self._default_domain = domain

    def _get_domain(self, domain: str | None = None) -> str:
        return domain or self._default_domain

    def _get_api_url(self, domain: str | None = None) -> str:
        domain = self._get_domain(domain)
        return f"https://api.mailgun.net/v3/{domain}/messages"

    async def send_message(self, params: SendMessageParams) -> str | None:
        """
        :return: None if successful sent, else error message.
        """

        if isinstance(params.to_addresses, str):
            to_addresses = params.to_addresses.strip().split(",")
        else:
            to_addresses = params.to_addresses

        from_address = f"{params.from_covirally_user}@{self._get_domain(params.domain)}"
        data = {
            "from": from_address,
            "to": to_addresses,
            "subject": params.subject,
            "text": params.text,
            "html": params.html,
            "template": params.template,
            "h:X-Mailgun-Variables": params.template_variables,
        }

        url = self._get_api_url(params.domain)
        if settings.app_env not in (AppEnvTypes.PROD, AppEnvTypes.DEV):
            logger.warning(f"Message is not actually to {to_addresses}. Check APP_ENV.")
            return None

        try:
            assert self.__api_key, "MAILGUN_API_KEY must be provided to send messages"
            response = await http_client.post(
                url, auth=("api", self.__api_key), data=data, timeout=5
            )
        except TimeoutException as exc:
            err = f"Timeout, can't send email to {to_addresses}: {exc}"
            logger.error(err)
            return err
        except AssertionError as exc:
            logger.error(str(exc))
            return str(exc)

        json_response = response.json()
        # error codes might be found here https://documentation.mailgun.com/en/latest/api-sending.html#examples  # noqa
        if response.status_code == 200:
            return None

        error_message: str
        if response.status_code == 400:
            error_message = json_response["message"]
            logger.error(error_message)
        elif response.status_code == 401:
            error_message = "Sending is forbidden. Probably, wrong API_KEY"
            logger.error(error_message)
        elif response.status_code == 404:
            error_message = f"Wrong domain in api url: {url}"
            logger.error(error_message)
        elif response.status_code == 413:
            error_message = "Request size exceeds 52.4MiB limit"
            logger.error(error_message)
        elif response.status_code == 429:
            error_message = json_response["message"]
            logger.error(error_message)
        else:
            error_message = json_response["message"]
        return error_message

    async def send_email_confirmation(
        self,
        *,
        verfiy_email_token: str,
        to_address: str,
        avatar_url: str | None = None,
        username: str | None = None,
    ) -> str | None:
        confirmation_url = (
            f"https://{settings.server_host}/auth/verifyemail/{verfiy_email_token}"
        )

        params = SendMessageParams(
            from_covirally_user="confirmemail",
            to_addresses=to_address,
            template="verify-email",
            subject="Email confirmation",
            template_variables=json.dumps(
                EmailConfirmationParams(
                    avatar=avatar_url or DEFAULT_AVATAR_URL,
                    username=username,
                    email=to_address,
                    confirm_link=confirmation_url,
                )
            ),
        )
        return await self.send_message(params)

    async def send_refresh_password(
        self,
        *,
        refresh_password_token: str,
        to_address: str,
        avatar_url: str | None,
        username: str | None,
    ) -> str | None:
        change_password_url = (
            f"https://{settings.frontend_host}/refresh-password/{refresh_password_token}"
        )

        params = SendMessageParams(
            from_covirally_user="no-reply",
            to_addresses=to_address,
            subject="Refresh password",
            template="forgot-password",
            template_variables=json.dumps(
                ForgotPasswordParams(
                    avatar=avatar_url or DEFAULT_AVATAR_URL,
                    username=username,
                    reset_link=change_password_url,
                )
            ),
        )
        return await self.send_message(params)


mailgun = MailgunClient(api_key=settings.mailgun_api_key)
