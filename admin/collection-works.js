/* Collection membership lives on each work, so both editing routes save the
 * same relationship. Reuse Decap's authenticated relation picker and editor. */
(function () {
    const { CMS, h, createClass } = window;
    const Relation = CMS.getWidget("relation").control;

    function workURL(collectionId, author, type, workSlug) {
        const params = new URLSearchParams();
        params.set("assign_zbirka", collectionId);
        if (author) params.set("assign_author", author);
        if (!workSlug) {
            params.set("zbirka", collectionId);
            if (author) params.set("author", author);
            if (type === "poetry-collection") params.set("type", "poetry");
        }
        const path = workSlug ? `entries/${workSlug.split("/").map(encodeURIComponent).join("/")}` : "new";
        return `#/collections/works/${path}?${params}`;
    }

    const CollectionWorks = createClass({
        getInitialState() {
            return { selected: "" };
        },
        shouldComponentUpdate() { return true; },
        render() {
            const { entry, value, field } = this.props;
            if (!value || entry.get("newRecord")) {
                return h("p", null, "Prvo spremi zbirku. Zatim ovdje možeš dodati postojeće ili novo djelo.");
            }
            const data = entry.get("data");
            const author = data.get("author") || "";
            const type = data.get("type") || "";
            const linkProps = { target: "_blank", rel: "noopener", className: "collection-work-action" };
            return h("div", { className: "collection-work-manager" },
                h("p", null, "Djelo će biti dodano ovoj zbirci kada ga spremiš u otvorenom uređivaču."),
                h("a", { ...linkProps, href: workURL(value, author, type) }, "+ Napiši novo djelo"),
                h("label", { htmlFor: this.props.forID }, "Dodaj postojeće djelo"),
                h(Relation, {
                    ...this.props,
                    field: field.set("widget", "relation").set("name", "_work_picker"),
                    value: this.state.selected,
                    onChange: (selected) => this.setState({ selected: selected || "" }),
                    queryHits: this.props.queryHits || [],
                }),
                this.state.selected && h("a", {
                    ...linkProps,
                    href: workURL(value, author, type, this.state.selected),
                }, "Otvori i dodaj u zbirku"),
                h("p", null, "Uređivač se otvara u novoj kartici. Ako djelo već pripada drugoj zbirci, spremanjem će se premjestiti u ovu.")
            );
        },
    });

    const WorkCollection = createClass({
        getInitialState() {
            const hash = window.location.hash;
            const params = new URLSearchParams(hash.split("?")[1] || "");
            const assignment = hash.startsWith("#/collections/works/")
                ? params.get("assign_zbirka") : null;
            return { assignment, author: params.get("assign_author") };
        },
        componentDidMount() {
            if (this.state.assignment !== null) {
                const { assignment, author } = this.state;
                this.changeCollection(assignment);
                if (author) window.queueMicrotask(() => {
                    window.ArchiveFields.setValue("author", author);
                    window.ArchiveFields.setValue("zbirka", assignment);
                });
                // Apply the link once. Reloading must not undo later edits.
                const url = new URL(window.location.href);
                const [route, query] = url.hash.split("?");
                const params = new URLSearchParams(query);
                params.delete("assign_zbirka");
                params.delete("assign_author");
                url.hash = route + (params.size ? `?${params}` : "");
                window.history.replaceState(null, "", url);
            }
        },
        changeCollection(value, metadata) {
            if (value !== this.props.value) {
                const author = metadata?.zbirka?.zbirke?.[value]?.author;
                if (author) window.ArchiveFields.setValue("author", author);
                // A position belongs to its old collection. Append automatically
                // when moving a work, after the sibling field has mounted.
                window.queueMicrotask(() => {
                    if (window.ArchiveFields) window.ArchiveFields.setValue("zbirka_order", "");
                });
            }
            this.props.onChange(value, metadata);
            if (this.state.assignment !== null) this.setState({ assignment: null });
        },
        shouldComponentUpdate() { return true; },
        render() {
            return h(Relation, {
                ...this.props,
                onChange: this.changeCollection,
                value: this.state.assignment !== null ? this.state.assignment : this.props.value,
                field: this.props.field.set("widget", "relation"),
                queryHits: this.props.queryHits || [],
            });
        },
    });

    CMS.registerWidget("collection-works", CollectionWorks);
    CMS.registerWidget("work-collection", WorkCollection);
}());
