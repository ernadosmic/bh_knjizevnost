/* Markdown import widget for works and authors.
 * The selected file is parsed locally in the browser. Nothing is uploaded
 * until the Decap entry itself is saved.
 */
(function () {
    const { CMS, h, createClass } = window;
    const controls = new Map();
    window.ArchiveFields = {
        getValue(name) {
            return controls.get(name)?.props.value;
        },
        setValue(name, value) {
            const control = controls.get(name);
            if (control) control.importValue(value);
        },
    };

    // Each field updates through Decap's own onChange callback, which also
    // clears validation errors. Keep its built-in control and validation.
    ["string", "text", "number", "select", "relation", "work-collection", "author-picker",
        "list", "boolean", "markdown", "image"].forEach((name) => {
        const widget = CMS.getWidget(name);
        const Control = createClass({
            getInitialState() { return { importRevision: 0 }; },
            componentDidMount() {
                this.registerControl();
            },
            componentDidUpdate(previousProps) {
                if (previousProps.field !== this.props.field) this.registerControl();
                if (previousProps.value !== this.props.value && this.props.field.get("import_target")) {
                    window.dispatchEvent(new CustomEvent("archive-field-change"));
                }
            },
            registerControl() {
                if (controls.get(this.importFieldName) === this) controls.delete(this.importFieldName);
                this.importFieldName = this.props.field.get("name");
                if (this.props.field.get("import_target")) {
                    controls.set(this.importFieldName, this);
                }
            },
            componentWillUnmount() {
                const fieldName = this.importFieldName;
                if (controls.get(fieldName) === this) controls.delete(fieldName);
            },
            shouldComponentUpdate() { return true; },
            importValue(value) {
                this.props.onChange(value);
                // Stateful editors (notably Markdown) must reload their
                // internal document when a file replaces the field value.
                this.setState({ importRevision: this.state.importRevision + 1 });
            },
            isValid() {
                return this.control && this.control.isValid ? this.control.isValid() : true;
            },
            render() {
                return h(widget.control, {
                    ...this.props,
                    key: this.state.importRevision,
                    ref: (control) => { this.control = control; },
                });
            },
        });
        CMS.registerWidget(name, Control, widget.preview, widget.schema);
    });

    function parseMarkdownFile(text, filename) {
        const normalized = String(text || "").replace(/^\uFEFF/, "").replace(/\r\n/g, "\n");
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

        if (!frontmatter.title && !frontmatter.name) {
            const heading = body.match(/^\s*#\s+(.+?)\s*#*\s*\n/);
            frontmatter.title = heading ? heading[1] : filename
                .replace(/\.(md|markdown)$/i, "")
                .replace(/^[a-z]{1,10}\d{2,10}[-_]/i, "")
                .replace(/[-_]+/g, " ").trim();
            if (heading) body = body.slice(heading[0].length);
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
            rows.push(["Ime", fm.name || fm.title || "(nije navedeno)"]);
            if (fm.birth_year) rows.push(["Rođen", fm.birth_year]);
            if (fm.death_year) rows.push(["Umro", fm.death_year]);
        } else {
            rows.push(["Naslov", fm.title || "(nije naveden)"]);
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

        componentWillUnmount() {
            this.readVersion = (this.readVersion || 0) + 1;
        },

        async readFile(file) {
            const version = this.readVersion = (this.readVersion || 0) + 1;
            this.setState({ error: "" });

            if (!file) return;

            const lower = file.name.toLowerCase();
            if (!lower.endsWith(".md") && !lower.endsWith(".markdown")) {
                this.setState({ error: "Odaberi Markdown datoteku (.md ili .markdown)." });
                return;
            }

            try {
                const text = await file.text();
                if (version !== this.readVersion) return;
                const payload = parseMarkdownFile(text, file.name);
                const kind = this.props.field.get("import_kind") || "work";
                const data = this.props.entry.get("data");
                const imported = window.applyMarkdownImport(
                    data.clear().set("import_md", JSON.stringify(payload)),
                    kind === "author" ? "authors" : "works"
                );
                imported.forEach((value, name) => {
                    const control = controls.get(name);
                    if (control) control.importValue(value);
                });
                // Keep a summary, but never overwrite subsequent manual edits
                // by applying this payload a second time in preSave.
                this.props.onChange(JSON.stringify({ ...payload, applied: true }));
            } catch (error) {
                if (version !== this.readVersion) return;
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
                    "details",
                    { className: "md-import-summary" },
                    h("summary", null, payload.filename),
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
                        "Podaci i tekst su uneseni u obrazac. Možeš ih urediti prije spremanja."
                    ),
                    h(
                        "button",
                        {
                            type: "button",
                            className: "md-import-clear",
                            onClick: () => this.props.onChange(""),
                        },
                        "Sakrij sažetak uvoza"
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
