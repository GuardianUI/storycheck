const path = require("path");
const Dotenv = require("dotenv-webpack");

module.exports = {
  entry: "./provider-generator.js",
  output: {
    filename: "provider.js",
    path: path.resolve(__dirname, "provider"),
  },
  plugins: [
    new Dotenv()
  ],
  stats: {
    colors: false,
    hash: false,
    version: false,
    timings: false,
    assets: false,
    chunks: false,
    modules: false,
    reasons: false,
    children: false,
    source: false,
    errors: false,
    errorDetails: false,
    warnings: false,
    publicPath: false
  }
};
