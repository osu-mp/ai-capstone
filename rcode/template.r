# install.packages(c('stringr', 'dplyr', 'lubridate', 'ggplot2'))


library(stringr)
library(dplyr)
library(lubridate)
library(ggplot2)


# number of minutes to plot prior to window start
window_pre_mins = {window_pre_mins}
# number of minutes to plot after window ends
window_post_mins = {window_post_mins}


plot_root <- "{lion_plot_root}/"
# dir where motion csvs are stored
# data_root = "C:/accel_data/cougars/F222_32664_/trailcam_test/MotionData_32664/"

# M201
data_root = "C:/accel_data/cougars/M201_20170_020116_120116/MotionData_0/"
# F209
# data_root = "C:/accel_data/cougars/F209_22262_030717_032819/MotionData_22262/"
# F202
# data_root = "C:/accel_data/cougars/F202_27905_010518_072219/MP_motion/MotionData_27905/"


#################################################################
# CHOOSE LION DATA

# Edit the fields below to choose the individual lion, date,
# and exact time span of accelerometery data you want to view


# vertical line to show time(s) of interest
window_low_min = {window_low_min}
window_low_sec = 0
window_high_min = {window_high_min}
window_high_sec = 0
time_window = 10      # number of minutes to plot on either side of surge

lion.name = "{lion_name}"
year = {year}
month = {month}
day = {day}
hour = {hour}  # + MST_offset
hour_high = hour
# min_low = 42; second_low = 00
# min_high = 59; second_high = 00

second_low = 00
second_high = 00

# vertical line to show time(s) of interest
window_low_hour = {hour}
window_low_sec = 0
window_high_hour = {hour}
window_high_sec = 0

second_low = 00
second_high = 00

min_low = window_low_min - window_pre_mins
if (min_low < 0){{
  min_low = 60 + min_low
  hour = hour - 1
}}

min_high = window_high_min + window_post_mins
if (min_high >= 60){{
  min_high = min_high - 60;
  hour_high = hour_high + 1;
}}

# added to file name
file_desc = "_{plot_type}_{Kill_ID}"


#################################################################
##Choose your directory where hourly accel files are stored

month_abbr = month.abb[month]
month = sprintf("%02d", strtoi(month)) # zero pad the month and day
day = sprintf("%02d", strtoi(day))

folders = sprintf("%s/%s %s/%s/", year, month, month_abbr, day)
csv_name = sprintf("%s-%s-%s.csv", year, month, day)
csv_path = paste(data_root, folders, csv_name, sep="")
accel <- read.csv(csv_path, skip = 1)



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

###
#plot
df <- data.frame(UTC, Xg, Yg, Zg) %>%
  filter(UTC >= time_low & UTC <= time_high)


time.text <- paste(lion.name, as.character(format(time_low, format = "%Y-%m-%d"), sep = " "))
fname_time <- paste(lion.name, as.character(format(time_low, format = "%Y-%m-%d__%H_%M_%S"), sep = " "))

plot_name <- paste(plot_root, fname_time, file_desc, ".png", sep="")

p <- ggplot(data = df, aes(x = UTC)) +
  geom_line(aes(y = Yg, color = "Y axis")) +
  geom_line(aes(y = Xg, color = "X axis")) +
  geom_line(aes(y = Zg, color = "Z axis")) +
  geom_vline(xintercept=window_low, color="yellow", linewidth=1) +
  geom_vline(xintercept=window_high, color="yellow", linewidth=1) +
  labs(x = time.text, y = "Acceleration (g's)") +
  ylim(-0.3, 0.3) +
  scale_color_manual(values = c("Y axis" = "black", "X axis" = "red", "Z axis" = "blue")) +
  theme(axis.title.y = element_text(size = 18, color="black"),
        axis.title.x = element_text(size = 18, color="black"),
        axis.text.x = element_text(size = 12),  # Adjust x-axis text size
        panel.grid.major = element_line(color = "darkgray", size = 0.2),
        panel.grid.minor = element_line(color = "lightgray", size = 0.1),  # minor grid lines
        plot.background = element_rect(fill = "transparent", color = NA)
  ) +
  guides(color = guide_legend(title = "Axis"))
  #geom_vline(xintercept=window_low, color="yellow", linewidth=1) +
  #geom_vline(xintercept=window_high, color="yellow", linewidth=1)


interval <- as.difftime(10, units = "secs")

p +
  scale_x_datetime(
    breaks = seq(min(df$UTC), max(df$UTC), by = interval),
    labels = scales::date_format("%H:%M:%S"))


# add vertical line at point of interest (WIP)
#p + geom_vline(xintercept=window_low, color="yellow", linewidth=1) +
#  geom_vline(xintercept=window_high, color="yellow", linewidth=1)

ggsave(plot_name, plot=p)
