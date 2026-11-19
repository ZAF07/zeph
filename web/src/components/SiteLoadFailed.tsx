import { CopyLoadFailed } from "@/components/CopyLoadFailed";
import { siteColumn } from "@/components/site-styles";

/**
 * What a public page shows when the website's Copy couldn't be read: the
 * Copy couldn't-load block in the site's column.
 *
 * @returns The error state.
 */
export function SiteLoadFailed() {
  return (
    <main className={`${siteColumn} py-14`}>
      <CopyLoadFailed />
    </main>
  );
}
