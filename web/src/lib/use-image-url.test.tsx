import { screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useImageUrl } from "@/lib/use-image-url";
import { renderWithQueries } from "@/test/render-with-queries";

const loadImage = vi.fn<() => Promise<Blob>>();

function ImageState({ hasImage = true }: { hasImage?: boolean }) {
  const image = useImageUrl(["test-image", "1"], loadImage, hasImage);
  if (image.failed) {
    return <p>failed</p>;
  }
  return <p>{image.url ?? "no url"}</p>;
}

describe("useImageUrl", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    URL.createObjectURL = vi.fn(() => "blob:image-1");
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("gives a URL for the loaded image and frees it when the component goes", async () => {
    loadImage.mockResolvedValue(new Blob(["image"]));
    const { unmount } = renderWithQueries(<ImageState />);

    expect(await screen.findByText("blob:image-1")).toBeInTheDocument();
    unmount();

    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:image-1");
  });

  it("loads an image once for every component showing it", async () => {
    loadImage.mockResolvedValue(new Blob(["image"]));
    renderWithQueries(
      <>
        <ImageState />
        <ImageState />
      </>,
    );

    expect(await screen.findAllByText("blob:image-1")).toHaveLength(2);
    expect(loadImage).toHaveBeenCalledTimes(1);
  });

  it("loads nothing when there is no image", () => {
    renderWithQueries(<ImageState hasImage={false} />);

    expect(screen.getByText("no url")).toBeInTheDocument();
    expect(loadImage).not.toHaveBeenCalled();
  });

  it("says when the image can't load", async () => {
    loadImage.mockRejectedValue(new Error("down"));
    renderWithQueries(<ImageState />);

    expect(await screen.findByText("failed")).toBeInTheDocument();
  });
});
