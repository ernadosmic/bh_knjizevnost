/* A single author field for choosing an author or adding one inline.
 * New names live in the draft value until preSave converts them to archive data. */
(function () {
    const { CMS, h, createClass } = window;
    const Relation = CMS.getWidget("relation").control;
    const read = (value, key) => value && (value.get ? value.get(key) : value[key]);

    const AuthorPicker = createClass({
        getInitialState() {
            return { adding: typeof this.props.value === "object" && Boolean(this.props.value) };
        },
        shouldComponentUpdate() { return true; },
        isValid() {
            const value = this.props.value;
            const name = typeof value === "string" ? value : read(value, "name");
            return String(name || "").trim()
                ? true : { error: "Odaberi autora ili upiši ime novog autora." };
        },
        render() {
            const { value, field, forID, onChange } = this.props;
            const adding = this.state.adding || (value && typeof value === "object");
            return h("div", { className: "author-picker" },
                h("div", { className: "author-picker-actions" },
                    h("button", {
                        type: "button", "aria-pressed": !adding,
                        onClick: () => { this.setState({ adding: false }); onChange(""); },
                    }, "Odaberi autora"),
                    h("button", {
                        type: "button", "aria-pressed": Boolean(adding),
                        onClick: () => { this.setState({ adding: true }); onChange({ name: "" }); },
                    }, "+ Dodaj autora")
                ),
                adding ? h("div", null,
                    h("input", {
                        id: forID,
                        className: this.props.classNameWrapper,
                        type: "text",
                        placeholder: "Ime i prezime ili naziv autora",
                        value: read(value, "name") || "",
                        onChange: (event) => onChange({ name: event.target.value }),
                    }),
                    h("p", { className: "editor-field-note" },
                        "Autor će biti dodan automatski. Biografiju možeš dopuniti kasnije.")
                ) : h(Relation, {
                    ...this.props,
                    field: field.set("widget", "relation"),
                    value: typeof value === "string" ? value : "",
                    queryHits: this.props.queryHits || [],
                })
            );
        },
    });

    CMS.registerWidget("author-picker", AuthorPicker);

    // Use Decap's native meta.path so a membership change moves the source file
    // in the same save. The work's filename is retained for existing entries.
    const WorkLocation = createClass({
        getInitialState() { return { folder: this.props.value || "" }; },
        shouldComponentUpdate() { return true; },
        componentDidMount() {
            this.active = true;
            this.changed = () => window.queueMicrotask(() => {
                if (this.active) this.syncFolder();
            });
            window.addEventListener("archive-field-change", this.changed);
            window.queueMicrotask(() => {
                if (!this.active) return;
                // A manually moved file may still contain old cached membership.
                // Read its actual folder before populating the editor controls.
                const folder = String(this.props.value || "").replace(/^\/+|\/+$/g, "");
                if (!this.props.entry.get("newRecord") && folder) {
                    const [author, collection = ""] = folder.split("/");
                    const fields = window.ArchiveFields;
                    if (fields.getValue("author") !== author) fields.setValue("author", author);
                    if ((fields.getValue("zbirka") || "") !== collection) {
                        fields.setValue("zbirka", collection);
                        fields.setValue("zbirka_order", "");
                    }
                }
                this.changed();
            });
        },
        componentWillUnmount() {
            this.active = false;
            window.removeEventListener("archive-field-change", this.changed);
        },
        syncFolder() {
            const fields = window.ArchiveFields;
            let author = fields.getValue("author");
            if (author && typeof author === "object") {
                const name = read(author, "name") || "";
                let id = read(author, "id") || window.slugify(name);
                if (!id && name.trim()) {
                    id = window.newArchiveId("autor");
                    fields.setValue("author", { name, id });
                }
                author = id;
            }
            if (!author) return;
            const folder = [author, fields.getValue("zbirka")].filter(Boolean).join("/");
            if (folder !== this.state.folder) this.setState({ folder });
            if (this.props.entry.get("newRecord") && this.props.value) {
                this.props.onChange("");
            } else if (!this.props.entry.get("newRecord") && folder !== this.props.value) {
                this.props.onChange(folder);
            }
        },
        render() {
            return h("p", { className: "editor-field-note" },
                this.state.folder || "Mapa će se odabrati automatski uz autora i zbirku.");
        },
    });
    CMS.registerWidget("work-location", WorkLocation);
}());
