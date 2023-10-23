import pytest
from django.core.management import call_command
from django.urls import reverse
from playwright.sync_api import Page, expect


def test_counter(live_server, page: Page):
    page.set_default_timeout(5_000)
    page.goto(str(live_server))

    message_content = page.get_by_test_id("message-content")
    initialized_from = page.get_by_test_id("message-initialized-from")

    expect(initialized_from).to_have_text("127.0.0.1")
    expect(message_content).to_have_text("( no message )")

    # Click on the first "+" button.
    page.get_by_role("button", name="+").first.click()
    expect(message_content).to_have_text(
        "Counter 'First counter' incremented to 1. Its new value is now 1001."
    )
    expect(page.get_by_role("textbox").first).to_have_value("€ 1,001")

    # Click on the first "-" button.
    page.get_by_role("button", name="-").first.click()
    expect(message_content).to_have_text(
        "Counter 'First counter' incremented to -1. Its new value is now 1000."
    )
    expect(page.get_by_role("textbox").first).to_have_value("€ 1,000")

    # Click on the second "+" button.
    page.get_by_role("button", name="+").nth(1).click()
    expect(message_content).to_have_text(
        "Counter 'Second counter' incremented to 1. Its new value is now 1001."
    )
    expect(page.get_by_role("textbox").nth(1)).to_have_value("€ 1,001")


@pytest.mark.django_db
def test_coffee(live_server, page: Page):
    call_command("load_coffee_beans")
    coffee_url = str(live_server) + reverse("coffee:index")

    page.set_default_timeout(5_000)
    page.goto(coffee_url)

    # Search by arabica and assert that filter works
    page.get_by_role("textbox").click()
    page.get_by_role("textbox").press_sequentially("arabica")
    expect(page.get_by_test_id("coffee-row")).to_have_count(1)

    # Click on the "Edit" button and assert that the inline form is shown
    page.get_by_test_id("coffee-edit-button").click()
    expect(page.get_by_test_id("coffee-edit-form")).to_be_visible()

    # Set the stock quantity to 101, save the form, and assert the form is closed
    # and the value is updated
    page.locator("#id_stock_quantity").fill("101")
    page.get_by_test_id("coffee-edit-form-save").click()
    expect(page.get_by_test_id("coffee-edit-form")).to_be_hidden()
    expect(page.get_by_test_id("coffee-stock-quantity")).to_have_text("101")

    # Click on the "Delete" button and assert the record is deleted.
    page.on("dialog", lambda dialog: dialog.accept())
    page.get_by_test_id("coffee-delete-button").click()
    expect(page.get_by_test_id("coffee-row")).to_have_count(0)
