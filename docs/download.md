
# Download


### Latest releases.

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GitHub Releases</title>
</head>
<body>
  <!-- <h1>Latest Releases for DreamWall-Animation/dwpicker</h1> -->
  <ul id="release-list">Loading...</ul>

  <script>
    // GitHub API URL for the releases of the repository
    const repo = "DreamWall-Animation/dwpicker";
    const apiUrl = `https://api.github.com/repos/${repo}/releases`;

    async function fetchReleases() {
      try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
          throw new Error(`GitHub API error: ${response.status}`);
        }
        const releases = await response.json();
        const limitedReleases = releases.slice(0, 10);

        // Populate the release list
        const releaseList = document.getElementById("release-list");
        releaseList.innerHTML = ""; // Clear the "Loading..." text
        limitedReleases.forEach(release => {
          const listItem = document.createElement("li");
          listItem.innerHTML = `
            <a href="${release.html_url}" target="_blank">${release.name}</a>
            - Released on ${new Date(release.published_at).toLocaleDateString()}
          `;
          releaseList.appendChild(listItem);
        });
      } catch (error) {
        console.error("Error fetching releases:", error);
        document.getElementById("release-list").textContent =
          "Unable to fetch releases. Please try again later.";
      }
    }

    // Fetch releases when the page loads
    fetchReleases();
  </script>
</body>
</html>
