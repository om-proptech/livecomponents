from pathlib import Path

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
        "Counter 'First counter' incremented by 1. Its new value is now 1001."
    )
    expect(page.get_by_role("textbox").first).to_have_value("€ 1,001")

    # Click on the first "-" button.
    page.get_by_role("button", name="-").first.click()
    expect(message_content).to_have_text(
        "Counter 'First counter' incremented by -1. Its new value is now 1000."
    )
    expect(page.get_by_role("textbox").first).to_have_value("€ 1,000")

    # Click on the second "+" button.
    page.get_by_role("button", name="+").nth(1).click()
    expect(message_content).to_have_text(
        "Counter 'Second counter' incremented by 1. Its new value is now 1001."
    )
    expect(page.get_by_role("textbox").nth(1)).to_have_value("€ 1,001")


@pytest.mark.django_db
def test_coffee(live_server, page: Page):
    call_command("load_coffee_beans")
    coffee_url = str(live_server) + reverse("coffee")

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


@pytest.mark.django_db
def test_modals(live_server, page: Page):
    modals_url = str(live_server) + reverse("modals")

    page.set_default_timeout(5_000)
    page.goto(modals_url)

    # Click on the "Send email" link and see that the modal is shown
    # and has text populated by the context.
    page.get_by_text("Send email").first.click()
    expect(page.get_by_test_id("modal").first).to_be_visible()
    expect(page.get_by_test_id("modal-title").first).to_have_text("Alice")
    expect(page.get_by_test_id("modal-body").first).to_have_text(
        "Send email to alice@example.com?"
    )

    # Click the "Close" button and see that the modal is hidden.
    page.get_by_test_id("modal-close").first.click()
    expect(page.get_by_test_id("modal").first).to_be_hidden()


def test_stateless_counter(live_server, page: Page):
    statelesscounter_url = str(live_server) + reverse("statelesscounter")

    page.set_default_timeout(5_000)
    page.goto(statelesscounter_url)

    count = page.locator("div", has_text="Count:").last
    expect(count).to_contain_text("Count: 0")

    page.get_by_role("button", name="+1").click()
    expect(count).to_contain_text("Count: 1")

    page.get_by_role("button", name="-1").click()
    expect(count).to_contain_text("Count: 0")


def test_uploads(live_server, page: Page):
    uploads_url = str(live_server) + reverse("uploads")

    page.set_default_timeout(5000)
    page.goto(uploads_url)

    coffee_csv = Path(__file__).parents[1] / "example" / "coffee.csv"
    page.set_input_files("input[name=csv_file]", coffee_csv)
    page.get_by_role("button", name="Upload").click()
    expect(page.get_by_test_id("filename")).to_have_text("coffee.csv")


def test_taskboard(live_server, page: Page):
    """End-to-end tour of the task board demo.

    Exercises the interaction of hierarchy commands (find_ancestor),
    update_state, ComponentClean, TriggerEvents, save_context in fills,
    the nested message block, no_morph, and RefreshPage.
    """
    page.set_default_timeout(5_000)
    page.goto(str(live_server) + reverse("taskboard"))

    todo = page.get_by_test_id("taskboard-column-todo")
    doing = page.get_by_test_id("taskboard-column-doing")
    cards = page.get_by_test_id("taskboard-card")

    # Initial state: four default tasks.
    expect(cards).to_have_count(4)

    # Add a task. The input is wrapped in {% no_morph %}, so it is replaced
    # (and thereby cleared) when the board re-renders.
    page.get_by_test_id("taskboard-add-input").fill("Write the docs")
    page.get_by_test_id("taskboard-add-button").click()
    expect(cards).to_have_count(5)
    expect(page.get_by_test_id("taskboard-add-input")).to_have_value("")

    # Toggle a card: only the card is swapped (the board keeps its state in
    # sync via ComponentClean), and a TriggerEvents toast fires.
    roast = todo.get_by_test_id("taskboard-card").filter(has_text="Roast the beans")
    roast.get_by_test_id("taskboard-card-toggle").click()
    expect(page.get_by_test_id("taskboard-toast")).to_contain_text("marked as done")

    # Move a card: the whole board re-renders (dirty deduplication), the
    # message component in the footer fill is updated via find_one, and the
    # save_context variable in the fill survives the standalone re-render.
    grind = todo.get_by_test_id("taskboard-card").filter(has_text="Grind the beans")
    grind.get_by_test_id("taskboard-card-move-doing").click()
    expect(
        doing.get_by_test_id("taskboard-card").filter(has_text="Grind the beans")
    ).to_have_count(1)
    expect(page.get_by_test_id("message-content")).to_contain_text("moved to")
    expect(page.get_by_test_id("taskboard-owner")).to_have_text("Coffee Team")

    # Highlight: the filter lives on the board; cards read it and re-render
    # with fresh kwargs (update_state).
    page.get_by_test_id("taskboard-highlight-input").press_sequentially("brew")
    expect(page.locator('[data-highlighted="true"]')).to_have_count(1)
    expect(page.locator('[data-highlighted="true"]')).to_contain_text("Brew the coffee")

    # Remove the added card.
    docs = todo.get_by_test_id("taskboard-card").filter(has_text="Write the docs")
    docs.get_by_test_id("taskboard-card-remove").click()
    expect(cards).to_have_count(4)

    # Reset: RefreshPage triggers a full page reload with default state.
    page.get_by_test_id("taskboard-reset-button").click()
    expect(cards).to_have_count(4)
    expect(page.get_by_test_id("taskboard-toast")).to_have_text("")
    expect(page.get_by_test_id("taskboard-highlight-input")).to_have_value("")
