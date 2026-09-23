// Loads the current schema, puts the guides in front of it, lists the release
// snapshots, and starts Scalar.
//
// Safety settings, each one on purpose:
// - no proxyUrl, and externalUrls point at a host that cannot resolve: Scalar never
//   routes a request, and so never a partner token, through proxy.scalar.com;
// - live "Try It" needs a CORS change on the API host first, so this version offers
//   copyable samples only. hideTestRequestButton would also remove the token box, so
//   site.css hides the button instead, and hideClientButton hides the client link;
// - persistAuth false: the token lives only in the open tab;
// - telemetry, the AI agent and the MCP button are off.
// The Content-Security-Policy in index.html enforces the same limit in the browser.

(async () => {
  const load = async (path, as = 'json') => {
    const response = await fetch(path, { cache: 'no-cache' });
    if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
    return as === 'text' ? response.text() : response.json();
  };

  const [gtoScore, fairPlay, guideIndex, versions] = await Promise.all([
    load('openapi/business/v4.json'),
    load('openapi/fairplay/v1.json'),
    load('guides/index.json'),
    load('openapi/business/releases.json'),
  ]);

  // Each product carries its own guides, in front of its own reference.
  const withGuides = async (spec, files) => {
    const guides = await Promise.all(files.map((file) => load(`guides/${file}`, 'text')));
    spec.info.description = [spec.info.description, ...guides].join('\n\n');
    return spec;
  };
  await Promise.all([
    withGuides(gtoScore, guideIndex['gto-score']),
    withGuides(fairPlay, guideIndex.fairplay),
  ]);

  // RFC 2606 reserves .invalid, so this host never resolves.
  const nowhere = 'https://scalar-disabled.invalid';
  const sources = [
    { title: 'GTO Score v4', slug: 'gto-score-v4', content: gtoScore, default: true },
    { title: 'FairPlay v1', slug: 'fairplay-v1', content: fairPlay },
    ...versions.releases
      .slice()
      .reverse()
      .map((release) => ({
        title: `GTO Score ${release.tag} (snapshot)`,
        slug: release.tag,
        url: `openapi/business/${release.file}`,
      })),
  ];

  window.Scalar.createApiReference('#app', {
    sources,
    theme: 'default',
    layout: 'modern',
    withDefaultFonts: false,
    hideTestRequestButton: false,
    hideClientButton: true,
    persistAuth: false,
    telemetry: false,
    showDeveloperTools: 'never',
    agent: { disabled: true },
    mcp: { disabled: true },
    documentDownloadType: 'json',
    externalUrls: {
      dashboardUrl: nowhere,
      registryUrl: nowhere,
      proxyUrl: nowhere,
      apiBaseUrl: nowhere,
    },
    authentication: { preferredSecurityScheme: 'BearerAuth' },
    defaultHttpClient: { targetKey: 'shell', clientKey: 'curl' },
    hiddenClients: {
      c: true,
      clojure: true,
      csharp: true,
      dart: true,
      fsharp: true,
      go: true,
      http: false,
      java: true,
      kotlin: true,
      objc: true,
      ocaml: true,
      php: true,
      powershell: true,
      r: true,
      ruby: true,
      rust: true,
      swift: true,
    },
    metaData: { title: 'GTO Wizard API' },
  });
})().catch((error) => {
  console.error(error);
  document.getElementById('load-error').hidden = false;
});
