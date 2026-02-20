const fs = require("fs");
const core = require("@actions/core");

async function generateSecuritySummary(github, context) {
  const prNumber = context.payload.pull_request?.number;

  if (!prNumber) {
    console.log("Not a PR, skipping summary");
    return;
  }

  const images = ["refiner-app", "refiner-lambda", "refiner-ops"];
  let message = `## 🔒 Security Scan Results\n\n`;

  let totalCritical = 0;
  let totalHigh = 0;
  let totalMedium = 0;
  let totalLow = 0;

  let detailsMessage = "";

  for (const image of images) {
    try {
      const results = JSON.parse(
        fs.readFileSync(`trivy-${image}-results.json`, "utf8"),
      );

      detailsMessage += `### 📦 ${image}\n\n`;

      let imageCritical = 0,
        imageHigh = 0,
        imageMedium = 0,
        imageLow = 0;

      if (results.Results) {
        for (const result of results.Results) {
          if (result.Vulnerabilities) {
            for (const vuln of result.Vulnerabilities) {
              switch (vuln.Severity) {
                case "CRITICAL":
                  imageCritical++;
                  break;
                case "HIGH":
                  imageHigh++;
                  break;
                case "MEDIUM":
                  imageMedium++;
                  break;
                case "LOW":
                  imageLow++;
                  break;
              }
            }
          }
        }
      }

      totalCritical += imageCritical;
      totalHigh += imageHigh;
      totalMedium += imageMedium;
      totalLow += imageLow;

      const total = imageCritical + imageHigh + imageMedium + imageLow;

      if (total === 0) {
        detailsMessage += `✅ **No vulnerabilities found**\n\n`;
      } else {
        detailsMessage += `| Severity | Count |\n|----------|-------|\n`;
        if (imageCritical > 0)
          detailsMessage += `| 🔴 Critical | ${imageCritical} |\n`;
        if (imageHigh > 0) detailsMessage += `| 🟠 High | ${imageHigh} |\n`;
        if (imageMedium > 0)
          detailsMessage += `| 🟡 Medium | ${imageMedium} |\n`;
        if (imageLow > 0) detailsMessage += `| ⚪ Low | ${imageLow} |\n`;
        detailsMessage += `\n`;
      }
    } catch (error) {
      detailsMessage += `⚠️ Could not parse results for ${image}\n\n`;
      console.error(`Error parsing ${image}:`, error);
    }
  }

  // Summary at the top
  const totalVulns = totalCritical + totalHigh + totalMedium + totalLow;
  if (totalVulns > 0) {
    message += `### ⚠️ Found ${totalVulns} vulnerabilities\n\n`;
    message += `| Severity | Total |\n|----------|-------|\n`;
    if (totalCritical > 0) message += `| 🔴 Critical | ${totalCritical} |\n`;
    if (totalHigh > 0) message += `| 🟠 High | ${totalHigh} |\n`;
    if (totalMedium > 0) message += `| 🟡 Medium | ${totalMedium} |\n`;
    if (totalLow > 0) message += `| ⚪ Low | ${totalLow} |\n`;
    message += `\n`;
  } else {
    message += `### ✅ No vulnerabilities found!\n\n`;
  }

  message += detailsMessage;
  message += `\n---\n`;
  message += `**View detailed results**: [Security tab](https://github.com/${context.repo.owner}/${context.repo.repo}/security/code-scanning)\n`;
  message += `*Last updated: ${new Date()
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d{3}Z$/, " UTC")}*`;

  // Warn if critical or high vulnerabilities found
  if (totalCritical > 0 || totalHigh > 0) {
    core.warning(
      `Found ${totalCritical} critical and ${totalHigh} high severity vulnerabilities`,
    );
  }

  // Update or create comment
  const comments = await github.rest.issues.listComments({
    issue_number: prNumber,
    owner: context.repo.owner,
    repo: context.repo.repo,
  });

  const botComment = comments.data.find(
    (comment) =>
      comment.user.login === "github-actions[bot]" &&
      comment.body.includes("Security Scan Results"),
  );

  if (botComment) {
    await github.rest.issues.updateComment({
      comment_id: botComment.id,
      owner: context.repo.owner,
      repo: context.repo.repo,
      body: message,
    });
    console.log("Updated existing security scan comment");
  } else {
    await github.rest.issues.createComment({
      issue_number: prNumber,
      owner: context.repo.owner,
      repo: context.repo.repo,
      body: message,
    });
    console.log("Created new security scan comment");
  }
}

module.exports = { generateSecuritySummary };
