/* Markdown import widget for works and authors.
 * The selected file is parsed locally in the browser. Nothing is uploaded
 * until the Decap entry itself is saved.
 */
(function () {
    const { CMS, h, createClass } = window;

    function parseMarkdownFile(text, filename) {
        const normalized = String(text || "").replace(/\r\n/g, "\n");
        const match = normalized.match(/^---\s*\n([\s\S]*?)\n---\s*\n?([\s\S]*)$/);
        let frontmatter = {};
        let body = normalized;

        if (match) {
            frontmatter = window.jsyaml.load(match[1]) || {};
            body = match[2] || "";
            if (typeof frontmatter !== "object" || Array.isArray(frontmatter)) {
                throw new Error("YAML front matter mora biti objekt sa poljima.");
            }
        }

        return {
            filename,
            frontmatter,
            body,
        };
    }

    function valueSummary(payload, kind) {
        const fm = payload.frontmatter || {};
        const rows = [];

        if (kind === "author") {
            rows.push(["Ime", fm.name || "(nije navedeno)"]);
            if (fm.birth_year) rows.push(["Rođen", fm.birth_year]);
            if (fm.death_year) rows.push(["Umro", fm.death_year]);
        } else {
            rows.push(["Naslov", fm.title || "(nije naveden)"]);
            rows.push(["ID", fm.id || fm.archive_id || "(nije naveden)"]);
            rows.push(["Autor", fm.author_name || fm.author || "(nije naveden)"]);
            if (fm.type) rows.push(["Vrsta", fm.type]);
        }

        rows.push(["Tekst", payload.body && payload.body.trim()
            ? payload.body.trim().split(/\s+/).length + " riječi"
            : "prazan"]);

        return rows;
    }

    const ImportMarkdown = createClass({
        getInitialState() {
            return {
                error: "",
                dragging: false,
            };
        },

        async readFile(file) {
            this.setState({ error: "" });

            if (!file) return;

            const lower = file.name.toLowerCase();
            if (!lower.endsWith(".md") && !lower.endsWith(".markdown")) {
                this.setState({ error: "Odaberi Markdown datoteku (.md ili .markdown)." });
                return;
            }

            try {
                const text = await file.text();
                const payload = parseMarkdownFile(text, file.name);
                this.props.onChange(JSON.stringify(payload));
            } catch (error) {
                this.setState({
                    error: "Datoteku nije moguće pročitati: " + (error.message || error),
                });
            }
        },

        parseValue() {
            if (!this.props.value) return null;
            try {
                return JSON.parse(this.props.value);
            } catch (_) {
                return null;
            }
        },

        render() {
            const isNew = Boolean(this.props.entry && this.props.entry.get("newRecord"));
            const payload = this.parseValue();
            const kind = this.props.field.get("import_kind") || "work";
            const rows = payload ? valueSummary(payload, kind) : [];

            if (!isNew) {
                return h(
                    "div",
                    { className: "md-import-panel md-import-disabled" },
                    h("p", null, "Uvoz .md datoteke dostupan je samo pri kreiranju novog unosa.")
                );
            }

            return h(
                "div",
                {
                    className: this.state.dragging
                        ? "md-import-panel md-import-dragging"
                        : "md-import-panel",
                    onDragOver: (event) => {
                        event.preventDefault();
                        this.setState({ dragging: true });
                    },
                    onDragLeave: () => this.setState({ dragging: false }),
                    onDrop: (event) => {
                        event.preventDefault();
                        this.setState({ dragging: false });
                        this.readFile(event.dataTransfer.files[0]);
                    },
                },
                h(
                    "label",
                    { className: "md-import-button" },
                    payload ? "Odaberi drugi .md" : "Odaberi .md datoteku",
                    h("input", {
                        type: "file",
                        accept: ".md,.markdown,text/markdown,text/plain",
                        onChange: (event) => this.readFile(event.target.files[0]),
                    })
                ),
                h("span", { className: "md-import-drop-note" }, " ili prevuci datoteku ovdje"),
                payload && h(
                    "div",
                    { className: "md-import-summary" },
                    h("strong", null, payload.filename),
                    h(
                        "dl",
                        null,
                        ...rows.flatMap(([label, value]) => [
                            h("dt", { key: label + "-dt" }, label),
                            h("dd", { key: label + "-dd" }, String(value)),
                        ])
                    ),
                    h(
                        "p",
                        null,
                        "Pri spremanju će se uvesti podržani podaci i Markdown tekst. Slugovi i javni URL generiraju se po pravilima arhiva."
                    ),
                    h(
                        "button",
                        {
                            type: "button",
                            className: "md-import-clear",
                            onClick: () => this.props.onChange(""),
                        },
                        "Ukloni datoteku"
                    )
                ),
                this.state.error && h(
                    "p",
                    { className: "md-import-error" },
                    this.state.error
                )
            );
        },
    });

    CMS.registerWidget("import-md", ImportMarkdown);
}());
