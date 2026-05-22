const fs = require("fs");

/**
 * Parse Trivy scan results and count vulnerabilities
 */
function parseScanResults(images) {
  let totalCritical = 0;
  let totalHigh = 0;
  let totalMedium = 0;
  let totalLow = 0;
  const imageResults = [];

  for (const image of images) {
    try {
      const results = JSON.parse(
        fs.readFileSync(`trivy-${image}-results.json`, "utf8"),
      );

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

      imageResults.push({
        name: image,
        critical: imageCritical,
        high: imageHigh,
        medium: imageMedium,
        low: imageLow,
        total: imageCritical + imageHigh + imageMedium + imageLow,
        vulnerabilities:
          results.Results?.flatMap((r) => r.Vulnerabilities ?? []) ?? [],
      });
    } catch (error) {
      console.error(`Error parsing ${image}:`, error);
      imageResults.push({
        name: image,
        error: true,
        errorMessage: error.message,
      });
    }
  }

  return {
    totalCritical,
    totalHigh,
    totalMedium,
    totalLow,
    totalVulns: totalCritical + totalHigh + totalMedium + totalLow,
    imageResults,
  };
}

/**
 * Format results as GitHub markdown comment
 */
function formatGitHubComment(scanResults, repoOwner, repoName) {
  const {
    totalCritical,
    totalHigh,
    totalMedium,
    totalLow,
    totalVulns,
    imageResults,
  } = scanResults;

  let message = `## 🔒 Security Scan Results\n\n`;

  // Summary at the top
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

  // Per-image breakdown
  for (const result of imageResults) {
    message += `### 📦 ${result.name}\n\n`;

    if (result.error) {
      message += `⚠️ Could not parse results for ${result.name}\n\n`;
    } else if (result.total === 0) {
      message += `✅ **No vulnerabilities found**\n\n`;
    } else {
      message += `| Severity | Count |\n|----------|-------|\n`;
      if (result.critical > 0)
        message += `| 🔴 Critical | ${result.critical} |\n`;
      if (result.high > 0) message += `| 🟠 High | ${result.high} |\n`;
      if (result.medium > 0) message += `| 🟡 Medium | ${result.medium} |\n`;
      if (result.low > 0) message += `| ⚪ Low | ${result.low} |\n`;
      message += `\n`;
    }
  }

  message += `\n---\n`;
  message += `**View detailed results**: [Security tab](https://github.com/${repoOwner}/${repoName}/security/code-scanning)\n`;
  message += `*Last updated: ${new Date()
    .toISOString()
    .replace("T", " ")
    .replace(/\.\d{3}Z$/, " UTC")}*`;

  return message;
}

/**
 * Format results as Slack message for scheduled scans
 */
function formatSlackMessage(
  scanResults,
  repoUrl,
  branch = "main",
  riskExceptionUrl = null,
) {
  const {
    totalCritical,
    totalHigh,
    totalMedium,
    totalLow,
    totalVulns,
    imageResults,
  } = scanResults;

  let color = "good"; // green
  let emoji = "✅";
  let statusText = "No vulnerabilities found";

  if (totalCritical > 0) {
    color = "danger"; // red
    emoji = "🔴";
    statusText = `${totalCritical} Critical vulnerabilities detected!`;
  } else if (totalHigh > 0) {
    color = "warning"; // yellow
    emoji = "🟠";
    statusText = `${totalHigh} High vulnerabilities detected`;
  } else if (totalVulns > 0) {
    color = "#808080"; // gray
    emoji = "ℹ️";
    statusText = `${totalVulns} Medium/Low vulnerabilities`;
  }

  const blocks = [
    {
      type: "header",
      text: {
        type: "plain_text",
        text: `${emoji} Security Scan: ${branch}`,
      },
    },
    {
      type: "section",
      text: {
        type: "mrkdwn",
        text: `*${statusText}*`,
      },
    },
    {
      type: "section",
      fields: [
        {
          type: "mrkdwn",
          text: `🔴 *Critical:* ${totalCritical}`,
        },
        {
          type: "mrkdwn",
          text: `🟠 *High:* ${totalHigh}`,
        },
        {
          type: "mrkdwn",
          text: `🟡 *Medium:* ${totalMedium}`,
        },
        {
          type: "mrkdwn",
          text: `⚪ *Low:* ${totalLow}`,
        },
      ],
    },
  ];

  // Add per-image breakdown
  const imageFields = imageResults
    .filter((r) => !r.error)
    .map((r) => {
      const icon = r.total === 0 ? "✅" : "⚠️";
      return {
        type: "mrkdwn",
        text: `${icon} *${r.name}:* ${r.critical}C / ${r.high}H / ${r.medium}M / ${r.low}L`,
      };
    });

  if (imageFields.length > 0) {
    blocks.push({
      type: "section",
      fields: imageFields,
    });
  }

  // Add link to GitHub Security tab
  blocks.push({
    type: "section",
    text: {
      type: "mrkdwn",
      text: `<${repoUrl}/security/code-scanning|View detailed results in GitHub Security tab>`,
    },
  });

  if (riskExceptionUrl) {
    blocks.push({
      type: "section",
      text: {
        type: "mrkdwn",
        text: `<${riskExceptionUrl}|📋 Download Risk Exception Template> (under Artifacts)`,
      },
    });
  }

  return {
    attachments: [
      {
        color: color,
        blocks: blocks,
      },
    ],
  };
}

/**
 * Send notification to Slack
 */
async function sendSlackNotification(
  scanResults,
  repoUrl,
  branch,
  webhookUrl,
  riskExceptionUrl = null,
) {
  const payload = formatSlackMessage(
    scanResults,
    repoUrl,
    branch,
    riskExceptionUrl,
  );

  const response = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    console.error("Failed to send Slack notification:", await response.text());
    throw new Error(`Slack notification failed: ${response.status}`);
  } else {
    console.log("Slack notification sent successfully");
  }
}

/**
 * Post or update PR comment
 */
async function postGitHubComment(scanResults, github, context) {
  const prNumber = context.payload.pull_request?.number;

  if (!prNumber) {
    console.log("Not a PR, skipping GitHub comment");
    return;
  }

  const message = formatGitHubComment(
    scanResults,
    context.repo.owner,
    context.repo.repo,
  );

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

/**
 * For PR scans - posts comment to PR
 */
async function generatePRSummary(github, context, core) {
  const images = ["refiner-app", "refiner-lambda", "refiner-ops"];

  // Parse all scan results
  const scanResults = parseScanResults(images);

  // Warn if critical or high vulnerabilities found
  if (scanResults.totalCritical > 0 || scanResults.totalHigh > 0) {
    core.warning(
      `Found ${scanResults.totalCritical} critical and ${scanResults.totalHigh} high severity vulnerabilities`,
    );
  }

  // Post GitHub comment
  await postGitHubComment(scanResults, github, context);
}

/**
 * For scheduled scans - sends Slack notification
 */
async function generateScheduledSummary(github, context, core) {
  const images = ["refiner-app", "refiner-lambda", "refiner-ops"];

  // Parse all scan results
  const scanResults = parseScanResults(images);

  // Warn if critical or high vulnerabilities found
  if (scanResults.totalCritical > 0 || scanResults.totalHigh > 0) {
    core.warning(
      `Found ${scanResults.totalCritical} critical and ${scanResults.totalHigh} high severity vulnerabilities`,
    );
  }

  // Send Slack notification if webhook is configured
  const slackWebhook = process.env.SLACK_WEBHOOK_URL;
  if (slackWebhook) {
    try {
      const repoUrl = `https://github.com/${context.repo.owner}/${context.repo.repo}`;
      const branch = context.ref.replace("refs/heads/", "");
      const riskExceptionUrl = process.env.RISK_EXCEPTION_URL || null;

      await sendSlackNotification(
        scanResults,
        repoUrl,
        branch,
        slackWebhook,
        riskExceptionUrl,
      );
    } catch (error) {
      console.error("Failed to send Slack notification:", error);
      core.setFailed(`Slack notification failed: ${error.message}`);
    }
  } else {
    console.log("SLACK_WEBHOOK_URL not configured, skipping notification");
  }
}

function generateRiskExceptionMarkdown(scanResults, generateForLevels) {
  const { imageResults } = scanResults;
  const date = new Date().toISOString().split("T")[0];

  let md = `# Security Risk Exception Request\n\n`;
  md += `**Date:** ${date}\n\n`;

  for (const result of imageResults) {
    if (result.error) continue;

    const actionableVulns = result.vulnerabilities.filter((v) =>
      generateForLevels.includes(v.Severity),
    );

    if (actionableVulns.length === 0) continue;

    md += `## ${result.name} image\n\n`;

    for (const vuln of actionableVulns) {
      const hasfix = vuln.FixedVersion
        ? `Yes — upgrade to ${vuln.FixedVersion}`
        : "No fix available";

      // The Aqua page takes a long time to update so the link often doesn't work.
      // We can try getting the NVD URL first and fallback to the Aqua URL if needed.
      const nvdURL = vuln.VulnerabilityID?.startsWith("CVE-")
        ? `https://nvd.nist.gov/vuln/detail/${vuln.VulnerabilityID}`
        : (vuln.PrimaryURL ?? "N/A");

      md += `### ${vuln.Severity}: ${vuln.VulnerabilityID}\n\n`;
      md += `| Field | Details |\n|---|---|\n`;
      md += `| **Package** | \`${vuln.PkgName}\` |\n`;
      md += `| **Installed Version** | \`${vuln.InstalledVersion}\` |\n`;
      md += `| **Fix Available** | ${hasfix} |\n`;
      md += `| **Title** | ${vuln.Title ?? "N/A"} |\n`;
      md += `| **Reference** | ${nvdURL} |\n\n`;

      md += `#### Risk Acceptance Justification\n\n`;
      md += `> _Why is this an acceptable risk?_\n\n`;
      md += `**Justification:** \n\n`;
      md += `**Mitigating Controls:** \n\n`;
      md += `**Remediation Timeline:** \n\n`;
      md += `---\n\n`;
    }
  }

  return md;
}

async function generateRiskExceptionTemplate(core) {
  const images = ["refiner-app", "refiner-lambda", "refiner-ops"];
  const generateForLevels = ["CRITICAL", "HIGH"];

  const scanResults = parseScanResults(images);

  const hasActionableVuln = scanResults.imageResults.some(
    (r) =>
      !r.error &&
      r.vulnerabilities?.some((v) => generateForLevels.includes(v.Severity)),
  );

  if (!hasActionableVuln) {
    core.info(
      `No vulnerabilities found for desired levels: ${generateForLevels.join(", ")}. Skipping risk exception template.`,
    );
    return;
  }

  const markdown = generateRiskExceptionMarkdown(
    scanResults,
    generateForLevels,
  );
  fs.writeFileSync("risk-exception.md", markdown);
  core.info("Risk exception template written to risk-exception.md");
}

module.exports = {
  generatePRSummary,
  generateScheduledSummary,
  generateRiskExceptionTemplate,
};
