/* Site-wide publishing control.
 *
 * The browser never calls the GitHub Actions API directly and never contains
 * a GitHub token. Clicking publish changes the private release request file
 * and uses Decap's normal authenticated Save action. GitHub Actions watches
 * that temporary cms/release/... branch and performs the batched release.
 */
(function () {
    const { CMS, h, createClass } = window;
    const RELEASE_ROUTE = "#/collections/release/entries/publish-site";
    const AUTO_KEY = "bh-knjizevnost-site-publish-auto";

    function findSaveButton() {
        return Array.from(document.querySelectorAll("button"))
            .find((button) => button.textContent.trim() === "Save");
    }

    function clickSaveWhenReady(component, attempt) {
        const save = findSaveButton();
        if (save && !save.disabled) {
            save.click();
            component.setState({
                running: true,
                message: "Šaljem zahtjev za objavu…",
                error: false,
            });
            return;
        }

        if (attempt < 80) {
            window.setTimeout(() => clickSaveWhenReady(component, attempt + 1), 75);
            return;
        }

        component.setState({
            running: false,
            message: "Nisam uspio pokrenuti spremanje. Pritisni Save iznad i pokušaj ponovo.",
            error: true,
        });
    }

    const SitePublish = createClass({
        getInitialState() {
            return {
                running: false,
                message: "Objavit će se sve trenutno sačuvane CMS izmjene, a stranica će se izgraditi samo jednom.",
                error: false,
            };
        },

        componentDidMount() {
            this._savedHandler = () => {
                this.setState({
                    running: false,
                    message: "Zahtjev je poslan. Objavljivanje svih sačuvanih izmjena je pokrenuto.",
                    error: false,
                });
            };
            window.addEventListener("site-wide-publish-saved", this._savedHandler);

            if (window.sessionStorage.getItem(AUTO_KEY) === "1") {
                window.sessionStorage.removeItem(AUTO_KEY);
                window.setTimeout(() => this.startPublish(false), 150);
            }
        },

        componentWillUnmount() {
            window.removeEventListener("site-wide-publish-saved", this._savedHandler);
        },

        startPublish(ask) {
            if (this.state.running) return;

            if (ask && !window.confirm(
                "Objaviti sve sačuvane izmjene na javnu stranicu? Stranica će se izgraditi jednom nakon objave."
            )) {
                return;
            }

            this.setState({
                running: true,
                message: "Pripremam objavu…",
                error: false,
            });

            this.props.onChange(new Date().toISOString());
            window.setTimeout(() => clickSaveWhenReady(this, 0), 50);
        },

        render() {
            return h(
                "div",
                { className: "site-publish-panel" },
                h(
                    "button",
                    {
                        type: "button",
                        className: "site-publish-primary",
                        disabled: this.state.running,
                        onClick: () => this.startPublish(true),
                    },
                    this.state.running ? "OBJAVLJUJEM…" : "OBJAVI STRANICU"
                ),
                h(
                    "p",
                    {
                        className: this.state.error
                            ? "site-publish-message site-publish-error"
                            : "site-publish-message",
                    },
                    this.state.message
                )
            );
        },
    });

    CMS.registerWidget("site-publish", SitePublish);

    CMS.registerEventListener({
        name: "postSave",
        handler: ({ collection }) => {
            if (collection && collection.get("name") === "release") {
                window.dispatchEvent(new CustomEvent("site-wide-publish-saved"));
            }
        },
    });

    function addShortcut() {
        const inCms = document.querySelector(
            '[class*="AppMainContainer"], [class*="EditorContainer"], [class*="CollectionContainer"]'
        );
        const existing = document.getElementById("site-wide-publish-shortcut");
        const onReleasePage = window.location.hash.startsWith(RELEASE_ROUTE);

        if (!inCms || onReleasePage) {
            if (existing) existing.remove();
            return;
        }

        if (existing) return;

        const button = document.createElement("button");
        button.id = "site-wide-publish-shortcut";
        button.type = "button";
        button.textContent = "OBJAVI STRANICU";
        button.addEventListener("click", () => {
            if (!window.confirm(
                "Objaviti sve sačuvane izmjene na javnu stranicu? Stranica će se izgraditi jednom nakon objave."
            )) {
                return;
            }

            window.sessionStorage.setItem(AUTO_KEY, "1");
            window.location.hash = RELEASE_ROUTE;
        });

        document.body.appendChild(button);
    }

    const observer = new MutationObserver(addShortcut);
    observer.observe(document.documentElement, { childList: true, subtree: true });
    window.addEventListener("hashchange", addShortcut);
    window.setTimeout(addShortcut, 750);
}());
