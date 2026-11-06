// Browser regressions: run against real Host base CSS + the98 CSS, not a mock
// cascade. Run these checks manually with the collection's local Project open.
export function checkSelectPicker() {
    if (!CSS.supports("appearance", "base-select") ||
        !CSS.supports("selector(select::picker-icon)") ||
        !CSS.supports("selector(select::picker(select))") ||
        matchMedia("(forced-colors: active)").matches) {
        return { skipped: "Customizable picker unavailable or forced colors active" }
    }
    const fixture = document.createElement("fieldset")
    fixture.innerHTML = `
        <legend>Select picker regression</legend>
        <select aria-label="Dropdown"><option hidden>Hidden</option><option selected>Selected</option><option>Other</option><option disabled>Disabled</option><optgroup label="Group"><option>Grouped option</option></optgroup></select>
        <select size="1" aria-label="Size one"><option>One</option></select>
        <select disabled aria-label="Disabled dropdown"><option>One</option></select>
        <select multiple aria-label="Multiple"><option>One</option></select>
        <select size="3" aria-label="List box"><option>One</option></select>
    `
    const previousFocus = document.activeElement
    document.body.append(fixture)
    const results = []
    const check = (condition, message) => {
        if (!condition) throw new Error(message)
        results.push(message)
    }
    try {
        const [dropdown, sizeOne, disabled, multiple, list] = fixture.querySelectorAll("select")
        for (const select of [dropdown, sizeOne, disabled]) {
            check(getComputedStyle(select).appearance === "base-select", "Dropdown uses customizable picker")
            check(getComputedStyle(select, "::picker-icon").display === "none", "No duplicate arrow")
        }
        for (const select of [multiple, list]) {
            check(getComputedStyle(select).appearance !== "base-select", "List box is not enhanced")
        }
        dropdown.focus()
        const picker = getComputedStyle(dropdown, "::picker(select)")
        check(picker.borderRadius === "0px", "Picker has square corners")
        check(picker.fontSize === getComputedStyle(dropdown).fontSize, "Picker inherits compact control font")
        check(picker.overflowX === "hidden" && picker.overflowY === "auto", "Picker scrolls vertically only")
        check(picker.scrollbarGutter === "stable", "Picker reserves space for classic vertical scrollbar")
        const optionStyle = getComputedStyle(dropdown.options[2])
        check(optionStyle.whiteSpace === "normal" && optionStyle.overflowWrap === "anywhere", "Long labels wrap rather than requiring horizontal scrolling")
        check(getComputedStyle(dropdown.options[0]).display === "none", "Hidden option stays hidden")
        check(getComputedStyle(dropdown.options[1], "::checkmark").display === "none", "No modern selection tick")
        // Override the existing theme tokens to prove options do not hardcode colors.
        dropdown.style.setProperty("--dialog-blue", "rgb(1, 2, 3)")
        dropdown.style.setProperty("--button-highlight", "rgb(240, 241, 242)")
        dropdown.style.setProperty("--text-color", "rgb(4, 5, 6)")
        dropdown.style.setProperty("--button-shadow", "rgb(100, 101, 102)")
        const selected = getComputedStyle(dropdown.options[1])
        const other = getComputedStyle(dropdown.options[2])
        check(selected.backgroundColor === "rgb(1, 2, 3)" && selected.color === "rgb(240, 241, 242)", "Selection uses theme tokens even when select is focused")
        check(other.backgroundColor === "rgb(240, 241, 242)" && other.color === "rgb(4, 5, 6)", "Unselected option uses theme tokens")
        check(getComputedStyle(dropdown.options[3]).color === "rgb(100, 101, 102)", "Disabled option uses theme token")
        check(getComputedStyle(dropdown.querySelector("optgroup")).color === "rgb(100, 101, 102)", "Group label uses gray theme token")
        const grouped = getComputedStyle(dropdown.options[4])
        check(grouped.color === "rgb(4, 5, 6)" && grouped.fontWeight === "400", "Grouped option keeps regular text styling")
        return { passed: results.length, results }
    } finally {
        fixture.remove()
        if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus()
    }
}

export function checkSelectArrows() {
    const fixture = document.createElement("fieldset")
    fixture.innerHTML = `
        <legend>Select arrow regression</legend>
        <select aria-label="Standalone regression select"><option>Standalone</option></select>
        <table><thead><tr><th>Select</th></tr></thead><tbody><tr><td>
            <select aria-label="Table regression select"><option>Table cell</option></select>
        </td></tr></tbody></table>
    `
    const previousFocus = document.activeElement
    document.body.append(fixture)
    const results = []
    try {
        for (const select of fixture.querySelectorAll("select")) {
            let normalImage = null
            for (const state of ["normal", "focus", "active", "focus-active", "disabled"]) {
                select.blur()
                select.disabled = state === "disabled"
                select.classList.toggle("active", state.includes("active"))
                if (state.includes("focus")) select.focus()
                const style = getComputedStyle(select)
                const snapshot = {
                    select: select.getAttribute("aria-label"), state,
                    image: style.backgroundImage, repeat: style.backgroundRepeat,
                    x: style.backgroundPositionX, y: style.backgroundPositionY,
                    paddingRight: style.paddingRight,
                }
                const fail = (message) => { throw new Error(`${snapshot.select} / ${state}: ${message}; ${JSON.stringify(snapshot)}`) }
                if (snapshot.image === "none") fail("arrow image missing")
                if (snapshot.repeat !== "no-repeat") fail("arrow must not tile")
                if (snapshot.x !== "calc(100% - 2px)" || snapshot.y !== "2px") fail("arrow must stay at top 2px right 2px")
                if (parseFloat(snapshot.paddingRight) < 32) fail("text must reserve arrow space")
                if (state === "normal") normalImage = snapshot.image
                if (state.includes("active") && snapshot.image === normalImage) fail("pressed arrow asset missing")
                results.push({ ...snapshot, image: "present" })
            }
        }
        return { passed: results.length, results }
    } finally {
        fixture.remove()
        if (previousFocus instanceof HTMLElement && previousFocus.isConnected) previousFocus.focus()
    }
}
