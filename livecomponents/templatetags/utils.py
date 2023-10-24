from contextlib import contextmanager

from django.template import Context
from django.template.base import FilterExpression, Parser, Token, TokenType
from django_components.templatetags.component_tags import safe_resolve


class CapturedTokens:
    def __init__(self):
        self.tokens = []

    def render(self):
        return render_tokens(self.tokens)

    def __str__(self):
        return f"CapturedTokens({self.render()!r})"

    def __repr__(self):
        return str(self)


@contextmanager
def capture_used_tokens(parser: Parser, token: Token):
    """Capture the tokens used by a template tag."""
    tokens_before = parser.tokens[:]
    captured_tokens = CapturedTokens()
    yield captured_tokens
    used_tokens = tokens_before[len(parser.tokens) :] + [token]
    captured_tokens.tokens = reversed(used_tokens)


def render_tokens(tokens: list[Token]) -> str:
    return "".join(render_token(token) for token in tokens)


def render_token(token: Token) -> str:
    if token.token_type == TokenType.TEXT:
        return token.contents
    elif token.token_type == TokenType.VAR:
        return "{{" + token.contents + "}}"
    elif token.token_type == TokenType.BLOCK:
        return "{% " + token.contents + " %}"
    elif token.token_type == TokenType.COMMENT:
        return "{# " + token.contents + " #}"
    raise ValueError(f"Unknown token type: {token.token_type}")


def get_save_context_vars(
    context_kwargs: dict[str, FilterExpression]
) -> FilterExpression | None:
    return context_kwargs.pop("save_context", None)


def render_save_context_vars(
    save_context_vars: FilterExpression | None, context: Context
) -> list[str]:
    if save_context_vars is None:
        return []
    resolved = safe_resolve(save_context_vars, context)
    return [value.strip() for value in resolved.split(",")]
