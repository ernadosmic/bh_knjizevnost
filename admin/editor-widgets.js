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
}());
