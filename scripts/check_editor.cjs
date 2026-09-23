/* Real CMS browser checks against Decap's in-memory test backend.
 * No login credentials, repository writes, or public publishing are used. */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const yaml = require('js-yaml');
const assert = require('node:assert/strict');
const root = path.join(__dirname, '..');

(async () => {
    const config = yaml.load(fs.readFileSync(path.join(root, 'admin/config.yml'), 'utf8'));
    Object.assign(config, { backend: { name: 'test-repo' }, local_backend: false, load_config_file: false, publish_mode: 'simple' });
    config.collections = config.collections.filter(collection => collection.name !== 'release');
    const html = fs.readFileSync(path.join(root, 'admin/index.html'), 'utf8')
        .replace('<script src="./site-publish.js"></script>', '')
        .replace('        init();', `        init({config: ${JSON.stringify(config)}});`);
    const browser = await chromium.launch({
        headless: true,
        ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : {}),
    });
    const page = await browser.newPage();
    page.setDefaultTimeout(15000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('http://localhost:4199/**', route => {
        const url = new URL(route.request().url());
        if (url.pathname === '/admin/') return route.fulfill({ contentType: 'text/html', body: html });
        const file = path.join(root, url.pathname);
        return route.fulfill({ contentType: file.endsWith('.js') ? 'text/javascript' : 'text/css', body: fs.readFileSync(file) });
    });
    const field = name => page.getByRole('textbox', { name, exact: true });
    const upload = (name, text) => page.locator('input[type=file]').setInputFiles({ name, mimeType: 'text/markdown', buffer: Buffer.from(text) });
    async function save() {
        await page.getByRole('button', { name: /^(Publish|Published)$/ }).click();
        await page.getByText('Publish now', { exact: true }).click();
        // The mobile layout hides the status badge, but it still marks completion.
        await page.getByText(/Changes saved/i).waitFor({ state: 'attached' });
        return page.evaluate(() => window.savedData);
    }
    async function newEntry(collection, query = '') {
        await page.evaluate(route => { location.hash = route; }, `#/collections/${collection}/new${query}`);
        await page.locator('input[type=file]').waitFor();
    }
    try {
        await page.goto('http://localhost:4199/admin/', { waitUntil: 'networkidle', timeout: 60000 });
        await page.getByRole('button', { name: /login/i }).click();
        await page.evaluate(() => CMS.registerEventListener({ name: 'preSave', handler: ({ entry }) => {
            window.savedData = entry.get('data').toJS();
        } }));

        await newEntry('works');
        assert.equal(await page.getByText('Trajni ID', { exact: true }).count(), 0);
        assert.equal(await page.getByText('Novi autor', { exact: true }).count(), 0);
        await upload('pjesma.md', '# Moja pjesma\n\nПрви стих\nДруги стих\n');
        await page.getByText('Први стих', { exact: false }).waitFor();
        assert.equal(await field('Naslov').inputValue(), 'Moja pjesma');
        await page.getByRole('button', { name: '+ Dodaj autora', exact: true }).click();
        await field('Autor').fill('Narodna pjesma');
        await field('Naslov').fill('Edited title');
        const first = await save();
        assert.match(first.id, /^D-[0-9a-f-]{36}$/);
        assert.equal(first.archive_id, first.id);
        assert.equal(first.author, 'narodna-pjesma');
        assert.equal(first.author_name, 'Narodna pjesma');
        assert.equal(first.script, 'cyrillic');
        assert.equal(first.title, 'Edited title');
        assert.equal(first.body.trim(), 'Први стих\nДруги стих');
        assert.equal(first.import_md, undefined);
        console.log('Passed: import without metadata, inferred title, inline author, automatic ID and script.');

        await field('Naslov').fill('Corrected title');
        const edited = await save();
        assert.equal(edited.id, first.id);
        assert.equal(edited.permalink, first.permalink);
        console.log('Passed: repeat saves preserve IDs and URLs.');

        await newEntry('works');
        await upload('NP0001-poem.md', '\uFEFF---\r\nid: NP0001\r\ntitle: Đerzelez Alija\r\nauthor: Narodna pjesma\r\ntype: poem\r\ngenres: [epika, narodna]\r\n---\r\nPrvi stih\r\nDrugi stih\r\n');
        await page.getByText('Prvi stih', { exact: false }).waitFor();
        assert.equal(await field('Autor').inputValue(), 'Narodna pjesma');
        await upload('broken.md', '---\ntitle: [\n---\nBroken');
        await page.locator('.md-import-error').waitFor();
        assert.equal(await field('Naslov').inputValue(), 'Đerzelez Alija');
        const imported = await save();
        assert.equal(imported.id, 'NP0001');
        assert.equal(imported.type, 'poetry');
        assert.deepEqual(imported.genres, ['epika', 'narodna']);
        console.log('Passed: legacy IDs, poem mapping, malformed-file recovery and metadata preservation.');

        await newEntry('authors');
        await upload('author.md', '---\nname: Isak Samokovlija\nbirth_year: 1889\n---\nBiografija autora.\n');
        await page.getByText('Biografija autora.', { exact: false }).waitFor();
        const author = await save();
        await field('Ime i prezime').fill('Corrected Author Name');
        const changedAuthor = await save();
        assert.equal(changedAuthor.id, author.id);
        assert.equal(changedAuthor.permalink, author.permalink);
        assert.equal(changedAuthor.birth_year, 1889);
        console.log('Passed: author import and name correction preserve permanent references.');

        await page.evaluate(() => { location.hash = '#/collections/zbirke/new'; });
        await field('Naslov zbirke').fill('Moja zbirka');
        const collection = await save();
        await field('Naslov zbirke').fill('Ispravljen naslov zbirke');
        const changedCollection = await save();
        assert.equal(changedCollection.id, collection.id);
        assert.equal(changedCollection.permalink, collection.permalink);
        console.log('Passed: collection title correction preserves membership and URLs.');

        await newEntry('works');
        await page.setViewportSize({ width: 390, height: 844 });
        await page.getByRole('button', { name: '+ Dodaj autora', exact: true }).click();
        assert.equal(await field('Autor').isVisible(), true);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
        await field('Naslov').fill('Ručno uneseno djelo');
        await page.getByRole('button', { name: 'Odaberi autora', exact: true }).click();
        await page.locator('.author-picker input').fill('Corrected');
        await page.locator('.author-picker').getByText('Corrected Author Name', { exact: false }).click();
        await page.locator('[contenteditable="true"]').fill('Ručno upisan tekst.');
        const manual = await save();
        assert.match(manual.id, /^D-/);
        assert.equal(manual.author, author.id);
        assert.equal(manual.body.trim(), 'Ručno upisan tekst.');
        assert.deepEqual(errors, []);
        console.log('Passed: manual entry on mobile needs only title, author and text; no browser runtime errors.');
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
