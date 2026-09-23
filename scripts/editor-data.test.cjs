const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const crypto = require('node:crypto');
const { fromJS } = require('immutable');

const html = fs.readFileSync(path.join(__dirname, '../admin/index.html'), 'utf8');
let save;
const context = vm.createContext({
    window: { crypto, CMS: { registerEventListener: ({ handler }) => { save = handler; } }, initCMS() {} },
});
vm.runInContext([...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].at(-1)[1], context);
function prepare(collection, data) {
    return save({ entry: fromJS({ collection, data }) }).toJS();
}
const work = { title: 'Isti naslov', author: { name: 'Narodna pjesma' }, body: 'Prvi stih\nDrugi stih', script: 'auto' };

test('new work IDs and URLs are unique without author counters', () => {
    const first = prepare('works', work);
    const second = prepare('works', work);
    assert.match(first.id, /^D-[0-9a-f-]{36}$/);
    assert.notEqual(first.id, second.id);
    assert.notEqual(first.permalink, second.permalink);
    assert.equal(first.archive_id, first.id);
    assert.equal(first.author, 'narodna-pjesma');
    assert.equal(first.author_name, 'Narodna pjesma');
    assert.equal(first.script, 'latin');
    const edited = prepare('works', { ...first, title: 'Ispravljen naslov' });
    assert.equal(edited.id, first.id);
    assert.equal(edited.permalink, first.permalink);
    assert.equal(edited.created_at, first.created_at);
});

test('legacy work identifiers and URLs remain unchanged', () => {
    const saved = prepare('works', { ...work, id: 'NP0001', slug: 'stari-naslov' });
    assert.equal(saved.id, 'NP0001');
    assert.equal(saved.permalink, '/djela/narodna-pjesma/stari-naslov/');
});

test('duplicating a work creates a new identity instead of copying hidden IDs', () => {
    const original = prepare('works', work);
    const duplicate = save({ entry: fromJS({ collection: 'works', newRecord: true, data: original }) }).toJS();
    assert.notEqual(duplicate.id, original.id);
    assert.notEqual(duplicate.permalink, original.permalink);
});

test('non-Latin names do not require manually supplied slugs', () => {
    const saved = prepare('works', { ...work, title: 'Пјесма', author: { name: 'Народни пјесник' } });
    assert.match(saved.author, /^autor-/);
    assert.equal(saved.author_name, 'Народни пјесник');
    assert.match(prepare('authors', { name: 'Писац' }).id, /^autor-/);
    assert.match(prepare('zbirke', { title: 'Пјесме' }).id, /^zbirka-/);
});

test('imported archive IDs survive hidden fields without overwriting edits', () => {
    const saved = prepare('works', { ...work, title: 'Edited', import_md: JSON.stringify({
        applied: true, filename: 'file.md', frontmatter: { id: 'NP0001', title: 'Old' }, body: 'Old text',
    }) });
    assert.equal(saved.id, 'NP0001');
    assert.equal(saved.title, 'Edited');
    assert.equal(saved.body, work.body);
    assert.equal(saved.import_md, undefined);
});

test('new imports without IDs receive automatic identities', () => {
    const saved = prepare('works', { ...work, import_md: JSON.stringify({
        filename: 'poem.md', frontmatter: { title: 'Pjesma', author: 'Narodna pjesma', type: 'poem' }, body: 'Stih',
    }) });
    assert.match(saved.id, /^D-/);
    assert.equal(saved.type, 'poetry');
    assert.equal(saved.author_name, 'Narodna pjesma');
});

test('script detection respects explicit metadata', () => {
    assert.equal(prepare('works', { ...work, body: 'Ово је пјесма.' }).script, 'cyrillic');
    assert.equal(prepare('works', { ...work, body: 'Ово је пјесма.', script: 'other' }).script, 'other');
});

test('name corrections preserve author and collection identities', () => {
    const author = prepare('authors', { id: 'old-author', name: 'Corrected Name' });
    assert.equal(author.id, 'old-author');
    assert.equal(author.permalink, '/autori/old-author/');
    const collection = prepare('zbirke', { id: 'old-collection', slug: 'old-collection', title: 'Corrected Title' });
    assert.equal(collection.id, 'old-collection');
    assert.equal(collection.permalink, '/zbirke/old-collection/');
});

test('missing content and author still prevent saving', () => {
    assert.throws(() => prepare('works', { ...work, body: '' }), /tekst/);
    assert.throws(() => prepare('works', { ...work, author: '' }), /autora/);
    assert.throws(() => prepare('works', { ...work, title: ' ' }), /naslov/);
});
