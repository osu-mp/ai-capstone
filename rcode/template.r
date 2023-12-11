# install.packages(c('stringr', 'dplyr', 'lubridate', 'ggplot2', "tidyr"))
# install.packages("devtools")

library(stringr)
library(dplyr)
library(lubridate)
library(ggplot2)
library(tools)
library(tidyr)

#################################################################
# CHOOSE LION DATA
# Edit the fields below to choose the individual lion, date,
# and exact time span of accelerometery data you want to view
# R Script inputs (filled in by python script)
csv_path = "{csv_path}"
lion.name = "{lion_name}"
year = {year}
month = {month}
day = {day}
day_low = day
day_high = day
hour = {hour}
hour_high = hour
plot_title = toTitleCase("{plot_type}")
minor_tick_interval = {minor_tick_interval}

window_pre_mins = {window_pre_mins}         # number of minutes to plot prior to window start
window_post_mins = {window_post_mins}       # number of minutes to plot after window ends

plot_name <- "{lion_plot_path}_{plot_type}_{Kill_ID}.png"             # path to save output plot image


# vertical line to show time(s) of interest
window_low_min = {window_low_min}
window_low_sec = 0
window_high_min = {window_high_min}
window_high_sec = 0


# min_low = 42; second_low = 00
# min_high = 59; second_high = 00

second_low = 00
second_high = 00

# conservative estimate: 10:24:40 PM - 10:25:15 PM
cons_window_low_hour = {cons_window_low_hour}
cons_window_low_min = {cons_window_low_min}
cons_window_low_sec = {cons_window_low_sec}
cons_window_high_hour = {cons_window_high_hour}
cons_window_high_min = {cons_window_high_min}
cons_window_high_sec = {cons_window_high_sec}

# liberal estimate: 10:24:30 PM - 10:25:15 PM
# lib_window_low_hour = {lib_window_low_hour}
# lib_window_low_min = {lib_window_low_min}
# lib_window_low_sec = {lib_window_low_sec}
lib_window_high_hour = {lib_window_high_hour}
lib_window_high_min = {lib_window_high_min}
lib_window_high_sec = {lib_window_high_sec}

stalk_start_hour = {stalk_start_hour}
stalk_start_min = {stalk_start_min}
stalk_start_sec = {stalk_start_sec}


# TODO liberal estimate

# vertical line to show time(s) of interest
window_low_hour = {hour}
window_low_sec = 0
window_high_hour = {hour}
window_high_sec = 0

second_low = 00
second_high = 00

min_low = window_low_min - window_pre_mins
while (min_low < 0){{
  min_low = 60 + min_low
  hour = hour - 1
}}

min_high = window_high_min + window_post_mins
while (min_high >= 60){{
  min_high = min_high - 60;
  hour_high = hour_high + 1;
}}

if (hour < 0){{
    hour = 0
    min_low = 0
    #hour = hour + 24
    #day_low = day_low - 1
}}

if (hour_high >= 24){{
    hour_high = 23
    min_high = 59
    #hour_high -= 24
    #day_high = day_high + 1
}}
# added to file name
file_desc = "_{plot_type}_{Kill_ID}"


accel <- read.csv(csv_path, skip=1) # directory where daily accel files are stored



#rename columns
accel <- accel %>%
  rename(X.Axis = Acc.X..g.,
         Y.Axis = Acc.Y..g.,
         Z.Axis = Acc.Z..g.)

#format the date column
utc_col = sprintf("%s-%s-%s", year, month, day)
accel$UTC.DateTime <- force_tz(strptime(paste(utc_col, accel$UTC.DateTime, sep = " "), format = "%Y-%m-%d %H:%M:%S"), tz = "UTC")

###Double check Hrz of collar
# filen = paste(as.character(filename), year, "/Month_", month, "/Day_", day, "/Data_", year, "-", str_pad(month, 2, pad="0"), "-", str_pad(day, 2, pad = "0"), "_", hour, ".csv", sep="")
# sr = 16 #sampling rate of accelerometer in hertz, F202 ONLY collar at 32, ALL OTHERS at 16

#combine UTC.DateTime and Milliseconds
accel$Milliseconds <- sprintf("%03d", accel$Milliseconds)

time_combined <- paste(as.character(accel$UTC.DateTime), as.character(accel$Milliseconds), sep = ".")

UTC <- strptime(time_combined, format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

#displays thousandths of a second
op <- options(digits.secs = 3)

#converts raw accelerometer data into g's
Xg = accel$X.Axis*64/1000
Yg = accel$Y.Axis*64/1000
Zg = accel$Z.Axis*64/1000

#make time objects for start and end times
time_low <- paste(paste(year, month, day, sep = "-"), paste(hour, min_low, second_low, sep = ":"))
time_low <- strptime(as.character(paste(time_low, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

time_high <- paste(paste(year, month, day, sep = "-"), paste(hour_high, min_high, second_high, sep = ":"))
time_high <- strptime(as.character(paste(time_high, "999", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

window_low <- paste(paste(year, month, day, sep = "-"), paste(window_low_hour, window_low_min, window_low_sec, sep = ":"))
window_low <- strptime(as.character(paste(window_low, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

window_high <- paste(paste(year, month, day, sep = "-"), paste(window_high_hour, window_high_min, window_high_sec, sep = ":"))
window_high <- strptime(as.character(paste(window_high, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

cons_window_low <- paste(paste(year, month, day, sep = "-"), paste(cons_window_low_hour, cons_window_low_min, cons_window_low_sec, sep = ":"))
cons_window_low <- strptime(as.character(paste(cons_window_low, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

cons_window_high <- paste(paste(year, month, day, sep = "-"), paste(cons_window_high_hour, cons_window_high_min, cons_window_high_sec, sep = ":"))
cons_window_high <- strptime(as.character(paste(cons_window_high, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

# lib_window_low <- paste(paste(year, month, day, sep = "-"), paste(lib_window_low_hour, lib_window_low_min, lib_window_low_sec, sep = ":"))
# lib_window_low <- strptime(as.character(paste(lib_window_low, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

lib_window_high <- paste(paste(year, month, day, sep = "-"), paste(lib_window_high_hour, lib_window_high_min, lib_window_high_sec, sep = ":"))
lib_window_high <- strptime(as.character(paste(lib_window_high, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")

stalk_window_start <- paste(paste(year, month, day, sep = "-"), paste(stalk_start_hour, stalk_start_min, stalk_start_sec, sep = ":"))
stalk_window_start <- strptime(as.character(paste(stalk_window_start, "001", sep = ".")), format = "%Y-%m-%d %H:%M:%OS", tz = "UTC")


###
#plot
df <- data.frame(UTC, Xg, Yg, Zg) %>%
  filter(UTC >= time_low & UTC <= time_high)


# time.text <- paste(lion.name, as.character(format(time_low, format = "%Y-%m-%d"), sep = " "))
# fname_time <- paste(lion.name, as.character(format(time_low, format = "%Y-%m-%d__%H_%M_%S"), sep = " "))



# p <- ggplot(data = df, aes(x = UTC)) +
#   geom_line(aes(y = Yg, color = "Y axis")) +
#   geom_line(aes(y = Xg, color = "X axis")) +
#   geom_line(aes(y = Zg, color = "Z axis")) +
#   geom_vline(xintercept=window_low, color="yellow", linewidth=1) +
#   geom_vline(xintercept=window_high, color="yellow", linewidth=1) +
#   labs(x = time.text, y = "Acceleration (g's)") +
#   ylim(-0.3, 0.3) +
#   scale_color_manual(values = c("Y axis" = "black", "X axis" = "red", "Z axis" = "blue")) +
#   theme(axis.title.y = element_text(size = 18, color="black"),
#         axis.title.x = element_text(size = 18, color="black"),
#         axis.text.x = element_text(size = 12),  # Adjust x-axis text size
#         panel.grid.major = element_line(color = "darkgray", size = 0.2),
#         panel.grid.minor = element_line(color = "lightgray", size = 0.1),  # minor grid lines
#         plot.background = element_rect(fill = "transparent", color = NA)
#   ) +
#   guides(color = guide_legend(title = "Axis"))


# interval <- as.difftime(10, units = "secs")

# START subplots

df_long <- tidyr::gather(df, variable, value, -UTC)
# df_long <- gather(df, key = "variable", value = "value", -UTC)
# df_long <- tidyr::pivot_longer(df, cols = -UTC, names_to = "variable", values_to = "value")


# Create a data frame specifically for legend entries of the vertical lines
legend_data <- data.frame(
  xpos = c(window_high, window_low),
  label = c("High", "Low")
)


p <- ggplot(data = df, aes(x = UTC)) +
  geom_line(aes(y = Yg, color = "Y axis")) +
  labs(x = "Time", y = "Acceleration (g's)") +
  ylim(-0.3, 0.3) +
  scale_color_manual(values = c("Y axis" = "black")) +
  theme(axis.title.y = element_text(size = 18, color = "black"),
        axis.title.x = element_text(size = 18, color = "black"),
        axis.text.x = element_text(size = 12),
        panel.grid.major = element_line(color = "darkgray", linewidth = 0.2),
        panel.grid.minor = element_line(color = "lightgray", linewidth = 0.1),
        plot.background = element_rect(fill = "white")#, color = NA)
  ) +
  guides(color = guide_legend(title = "Axis")) +

  facet_wrap(~ variable, scales = "free_y", ncol = 1)

# df_long <- tidyr::gather(df, variable, value, -UTC)
df_long <- tidyr::pivot_longer(df, cols = -UTC, names_to = "variable", values_to = "value")

ggplot(df_long, aes(x = UTC, y = value, color = variable)) +
  geom_line() +
  labs(x = "Time", y = "Acceleration (g's)") +
  ylim(-0.3, 0.3) +
  scale_color_manual(values = c("Yg" = "black", "Xg" = "red", "Zg" = "blue")) +
  theme(axis.title.y = element_text(size = 18, color = "black"),
        axis.title.x = element_text(size = 18, color = "black"),
        axis.text.x = element_text(size = 12),
        panel.grid.major = element_line(color = "darkgray", linewidth = 0.2),
        panel.grid.minor = element_line(color = "lightgray", linewidth = 0.1),
        plot.background = element_rect(fill = "white")#, color = NA)
  ) +
  guides(color = guide_legend(title = "Axis"))+
  facet_wrap(~variable, scales = "free_y", ncol = 1)


p <- ggplot(data = df_long, aes(x = UTC, y = value, color = variable)) +
  geom_line() +
  labs(x = "Time", y = "Acceleration (g's)") +
  ylim(-0.3, 0.3) +
  scale_color_manual(values = c("Yg" = "black", "Xg" = "red", "Zg" = "blue")) +
  theme(axis.title.y = element_text(size = 18, color = "black"),
        axis.title.x = element_text(size = 18, color = "black"),
        axis.text.x = element_text(size = 12),
        panel.grid.major = element_line(color = "darkgray", linewidth = 0.2),
        panel.grid.minor = element_line(color = "lightgray", linewidth = 0.1),
        plot.background = element_rect(fill = "white")# color = NA)
  ) +
  guides(color = guide_legend(title = "Axis")) +
  facet_wrap(~ variable, scales = "free_y", ncol = 1)

#p <- p +
#  geom_vline(data = data.frame(xpos = c(window_high, window_low)),
#             aes(xintercept = as.numeric(xpos)), color = "yellow", linetype = "dashed")

# Plotting
p <- ggplot(data = df_long, aes(x = UTC, y = value, color = variable)) +
  geom_line() +
  labs(x = "Time", y = "Acceleration (g's)") +
  ylim(-0.3, 0.3) +
  scale_color_manual(values = c("Yg" = "black", "Xg" = "red", "Zg" = "blue")) +
  theme(
    axis.title.y = element_text(size = 18, color = "black"),
    axis.title.x = element_text(size = 18, color = "black"),
    axis.text.x = element_text(size = 12),
    panel.grid.major = element_line(color = "darkgray", linewidth = 0.2),
    panel.grid.minor = element_line(color = "lightgray", linewidth = 0.1),
    plot.background = element_rect(fill = "white")#, color = NA)
  ) +
  guides(color = guide_legend(title = "Axis")) +
  facet_wrap(~variable, scales = "free_y", ncol = 1)


# Adding vertical lines and mapping them to linetype with a manual scale for legend
p <- p +
  geom_vline(
    data = data.frame(xpos = c(window_high, window_low), label = c("Original", "Low")),
    aes(xintercept = as.numeric(xpos), linetype = "Original"),
    color = "orange", alpha = 0.3
  ) +
  geom_vline(
    data = data.frame(xpos = c(cons_window_low), label = c("KillStart")),
    aes(xintercept = as.numeric(xpos), linetype = "KillStart"),
    color = "darkred", alpha = 0.8
  ) +
  geom_vline(
    data = data.frame(xpos = c(cons_window_high), label = c("Conservative")),
    aes(xintercept = as.numeric(xpos), linetype = "Conservative"),
    color = "green", alpha = 0.9
  ) +
  geom_vline(
    data = data.frame(xpos = c(lib_window_high), label = c("Liberal")),
    aes(xintercept = as.numeric(xpos), linetype = "Liberal"),
    color = "darkblue", alpha = 0.9
  ) +
  geom_vline(
    data = data.frame(xpos = c(stalk_window_start), label = c("StalkStart")),
    aes(xintercept = as.numeric(xpos), linetype = "StalkStart"),
    color = "yellow", alpha = 0.75
  ) +
  scale_linetype_manual(
    name = "Surge Windows",
    values = c("Original" = "solid",
                "KillStart" = "solid",
                "Conservative" = "dashed", "Liberal" = "dashed", "StalkStart" = "solid"),
    labels = c("KillOrig", "KillStart", "KillEndCons", "KillEndLib", "StalkStart"),
    guide = guide_legend(
      override.aes = list(
        linetype = c("solid", "solid", "dashed", "dashed", "solid"),  # Assigning linetypes to Colby and Conservative
        color = c("orange", "darkred", "green", "darkblue", "yellow")  # Assigning colors to Colby and Conservative in the legend
      )
    )
  )

# Calculate the minimum and maximum timestamps
min_time <- min(df$UTC)
max_time <- max(df$UTC)

# Define the interval for minor breaks in seconds
minor_interval <- minor_tick_interval  # For example, every 5 seconds

# Generate minor breaks at the specified interval
minor_breaks <- seq.POSIXt(from = min_time, to = max_time, by = minor_interval)

# add title
p <- p +
  ggtitle(plot_title) +
  theme(
    plot.title = element_text(hjust = 0.5)  # Center title horizontally
  )


# END subplots
p = p +
  scale_x_datetime(
    #breaks = seq(min(df$UTC), max(df$UTC), by = interval),
    #labels = scales::date_format("%H:%M:%S"),
    minor_breaks = minor_breaks
    )
p
ggsave(plot_name, plot=p)

