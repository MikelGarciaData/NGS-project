library(tidyverse)
library(viridis)

df <- readr::read_tsv("mock_soil_species_10clades_300species.tsv")  # species, clade, freq

n_bins <- 200

qdf <- df %>%
  mutate(freq = as.numeric(freq)) %>%
  group_by(clade) %>%
  summarise(
    q = list(as.numeric(quantile(freq, probs = seq(0, 1, length.out = n_bins), na.rm = TRUE))),
    .groups = "drop"
  ) %>%
  mutate(bin = map(q, seq_along)) %>%     # <-- guaranteed 1..n_bins
  unnest(c(bin, q))

ggplot(qdf, aes(x = clade, y = bin, fill = q)) +
  geom_raster() +
  scale_fill_viridis_c(
    option = "magma",
    name = "Freq (quantiles)",
    limits = c(0, 1),
    oob = scales::squish  # avoids dropping if slight out-of-range happens in real data
  ) +
  labs(x = "Clade", y = NULL) +
  theme_minimal(base_size = 11) +
  theme(
    panel.grid = element_blank(),
    axis.text.y = element_blank(),
    axis.ticks = element_blank(),
    axis.text.x = element_text(angle = 90, vjust = 0.5, hjust = 1)
  )
