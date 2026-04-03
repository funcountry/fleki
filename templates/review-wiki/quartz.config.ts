import { QuartzConfig } from "./quartz/cfg"
import * as Plugin from "./quartz/plugins"

const config: QuartzConfig = {
  configuration: {
    pageTitle: "Fleki Knowledge Review",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    analytics: null,
    locale: "en-US",
    baseUrl: "localhost",
    ignorePatterns: [],
    defaultDateType: "modified",
    theme: {
      fontOrigin: "googleFonts",
      cdnCaching: true,
      typography: {
        header: "IBM Plex Sans",
        body: "Source Serif 4",
        code: "IBM Plex Mono",
      },
      colors: {
        lightMode: {
          light: "#f6f2ea",
          lightgray: "#ddd5ca",
          gray: "#b1a99e",
          darkgray: "#5c564d",
          dark: "#22201d",
          secondary: "#28536b",
          tertiary: "#658b6f",
          highlight: "rgba(40, 83, 107, 0.12)",
          textHighlight: "#efe28c88",
        },
        darkMode: {
          light: "#171816",
          lightgray: "#373731",
          gray: "#68675f",
          darkgray: "#d7d2c7",
          dark: "#f4efe7",
          secondary: "#9bc0d1",
          tertiary: "#8dbf91",
          highlight: "rgba(155, 192, 209, 0.12)",
          textHighlight: "#a08f2288",
        },
      },
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({
        priority: ["frontmatter", "git", "filesystem"],
      }),
      Plugin.SyntaxHighlighting({
        theme: {
          light: "github-light",
          dark: "github-dark",
        },
        keepBackground: false,
      }),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlEmbed: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({ markdownLinkResolution: "shortest" }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [Plugin.RemoveDrafts()],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.ContentIndex({
        enableSiteMap: false,
        enableRSS: false,
      }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.Favicon(),
      Plugin.NotFoundPage(),
    ],
  },
}

export default config
