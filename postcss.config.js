/**
 * PostCSS Configuration
 * 
 * Configures the CSS processing pipeline with TailwindCSS and Autoprefixer.
 * This setup enables modern CSS features and utility-first styling while
 * maintaining browser compatibility.
 * 
 * Plugins:
 * - TailwindCSS: Utility-first CSS framework for rapid UI development
 * - Autoprefixer: Automatically adds vendor prefixes for broader browser support
 * 
 * Note: Order of plugins matters - TailwindCSS must run before Autoprefixer
 */

module.exports = {
  plugins: {
    // Process Tailwind directives and utilities
    tailwindcss: {},
    // Add vendor prefixes automatically
    autoprefixer: {},
  },
}
