export interface ScoreCheckpoint {
  x: number;
  y: number;
}

export const checkpoints: ScoreCheckpoint[] = [
  { x: 0, y: 15 },
  { x: 10, y: 25 },
  { x: 20, y: 35 },
  { x: 30, y: 44 },
  { x: 40, y: 51 },
  { x: 50, y: 60 },
  { x: 60, y: 67 },
  { x: 70, y: 74 },
  { x: 80, y: 82 },
  { x: 90, y: 91 },
  { x: 100, y: 100 },
];

export function adjustMatchScore(originalScore: number): number {
  if (
    typeof originalScore !== "number" ||
    !Number.isFinite(originalScore) ||
    originalScore < 0 ||
    originalScore > 100
  ) {
    throw new RangeError("Score must be a number between 0 and 100.");
  }

  for (let i = 0; i < checkpoints.length - 1; i++) {
    const { x: x0, y: y0 } = checkpoints[i];
    const { x: x1, y: y1 } = checkpoints[i + 1];

    if (originalScore >= x0 && originalScore <= x1) {
      const ratio = (originalScore - x0) / (x1 - x0);
      const adjustedScore = y0 + ratio * (y1 - y0);

      return Math.round(adjustedScore * 10) / 10;
    }
  }

  return originalScore;
}
