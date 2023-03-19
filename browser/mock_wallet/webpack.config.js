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
    hash: true,
    colors: true,
    version: true,
    timings: true,
    assets: true,
    chunks: true,
    modules: true,
    reasons: true,
    children: false,
    source: true,
    errors: true,
    errorDetails: true,
    warnings: true,
    publicPath: true
  }
};
