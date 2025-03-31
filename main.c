#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <math.h>

#define MAX_LINE 2048
#define MAX_FIELDS 16
#define MAX_FIELD_LEN 256

typedef struct {
  char date[16];
  char month[8];
  double amount;
  int is_inflow;
  char category[64];
  int restricted;
} Entry;

typedef struct {
  char month[8];
  double inflow;
  double outflow;
} MonthStat;

typedef struct {
  char name[64];
  double outflow;
  int count;
} CategoryStat;

typedef struct {
  MonthStat *items;
  size_t count;
  size_t cap;
} MonthList;

typedef struct {
  CategoryStat *items;
  size_t count;
  size_t cap;
} CategoryList;

static void trim(char *s) {
  char *start = s;
  while (isspace((unsigned char)*start)) start++;
  if (*start == '\0') {
    *s = '\0';
    return;
  }
  if (start != s) {
    memmove(s, start, strlen(start) + 1);
  }
  char *end = s + strlen(s) - 1;
  while (end > s && isspace((unsigned char)*end)) end--;
  *(end + 1) = '\0';
}

static void normalize_key(const char *src, char *dst, size_t dst_len) {
  size_t j = 0;
  for (size_t i = 0; src[i] != '\0' && j + 1 < dst_len; i++) {
    char c = (char)tolower((unsigned char)src[i]);
    if (c == ' ' || c == '_' || c == '-') {
      continue;
    }
    dst[j++] = c;
  }
  dst[j] = '\0';
}

static int parse_csv_line(const char *line, char fields[][MAX_FIELD_LEN], int max_fields) {
  int field = 0;
  int in_quotes = 0;
  size_t len = strlen(line);
  size_t idx = 0;

  for (int i = 0; i < max_fields; i++) {
    fields[i][0] = '\0';
  }

  for (size_t i = 0; i <= len; i++) {
    char c = line[i];
    if (c == '\0' || c == '\n') {
      fields[field][idx] = '\0';
      trim(fields[field]);
      return field + 1;
    }

    if (in_quotes) {
      if (c == '"') {
        if (line[i + 1] == '"') {
          if (idx + 1 < MAX_FIELD_LEN) {
            fields[field][idx++] = '"';
          }
          i++;
        } else {
          in_quotes = 0;
        }
      } else {
        if (idx + 1 < MAX_FIELD_LEN) {
          fields[field][idx++] = c;
        }
      }
    } else {
      if (c == '"') {
        in_quotes = 1;
      } else if (c == ',') {
        fields[field][idx] = '\0';
        trim(fields[field]);
        field++;
        idx = 0;
        if (field >= max_fields) {
          return field;
        }
      } else if (c != '\r') {
        if (idx + 1 < MAX_FIELD_LEN) {
          fields[field][idx++] = c;
        }
      }
    }
  }
  return field + 1;
}

static int is_truthy(const char *value) {
  char buf[32];
  size_t len = strlen(value);
  if (len >= sizeof(buf)) len = sizeof(buf) - 1;
  for (size_t i = 0; i < len; i++) {
    buf[i] = (char)tolower((unsigned char)value[i]);
  }
  buf[len] = '\0';
  return strcmp(buf, "yes") == 0 || strcmp(buf, "y") == 0 || strcmp(buf, "true") == 0 || strcmp(buf, "1") == 0;
}

static int is_inflow_type(const char *value) {
  char buf[32];
  size_t len = strlen(value);
  if (len >= sizeof(buf)) len = sizeof(buf) - 1;
  for (size_t i = 0; i < len; i++) {
    buf[i] = (char)tolower((unsigned char)value[i]);
  }
  buf[len] = '\0';
  return strcmp(buf, "inflow") == 0 || strcmp(buf, "income") == 0 || strcmp(buf, "credit") == 0 || strcmp(buf, "grant") == 0 || strcmp(buf, "deposit") == 0;
}

static int is_outflow_type(const char *value) {
  char buf[32];
  size_t len = strlen(value);
  if (len >= sizeof(buf)) len = sizeof(buf) - 1;
  for (size_t i = 0; i < len; i++) {
    buf[i] = (char)tolower((unsigned char)value[i]);
  }
  buf[len] = '\0';
  return strcmp(buf, "outflow") == 0 || strcmp(buf, "expense") == 0 || strcmp(buf, "debit") == 0 || strcmp(buf, "spend") == 0 || strcmp(buf, "withdrawal") == 0;
}

static void month_list_add(MonthList *list, const char *month, double inflow, double outflow) {
  for (size_t i = 0; i < list->count; i++) {
    if (strcmp(list->items[i].month, month) == 0) {
      list->items[i].inflow += inflow;
      list->items[i].outflow += outflow;
      return;
    }
  }
  if (list->count == list->cap) {
    size_t next_cap = list->cap == 0 ? 16 : list->cap * 2;
    MonthStat *next = realloc(list->items, next_cap * sizeof(MonthStat));
    if (!next) {
      fprintf(stderr, "Memory allocation failed for months.\n");
      exit(1);
    }
    list->items = next;
    list->cap = next_cap;
  }
  strncpy(list->items[list->count].month, month, sizeof(list->items[list->count].month) - 1);
  list->items[list->count].month[7] = '\0';
  list->items[list->count].inflow = inflow;
  list->items[list->count].outflow = outflow;
  list->count++;
}

static void category_list_add(CategoryList *list, const char *name, double outflow) {
  for (size_t i = 0; i < list->count; i++) {
    if (strcmp(list->items[i].name, name) == 0) {
      list->items[i].outflow += outflow;
      list->items[i].count += 1;
      return;
    }
  }
  if (list->count == list->cap) {
    size_t next_cap = list->cap == 0 ? 16 : list->cap * 2;
    CategoryStat *next = realloc(list->items, next_cap * sizeof(CategoryStat));
    if (!next) {
      fprintf(stderr, "Memory allocation failed for categories.\n");
      exit(1);
    }
    list->items = next;
    list->cap = next_cap;
  }
  strncpy(list->items[list->count].name, name, sizeof(list->items[list->count].name) - 1);
  list->items[list->count].name[sizeof(list->items[list->count].name) - 1] = '\0';
  list->items[list->count].outflow = outflow;
  list->items[list->count].count = 1;
  list->count++;
}

static int compare_months(const void *a, const void *b) {
  const MonthStat *ma = (const MonthStat *)a;
  const MonthStat *mb = (const MonthStat *)b;
  return strcmp(ma->month, mb->month);
}

static int compare_categories(const void *a, const void *b) {
  const CategoryStat *ca = (const CategoryStat *)a;
  const CategoryStat *cb = (const CategoryStat *)b;
  if (cb->outflow > ca->outflow) return 1;
  if (cb->outflow < ca->outflow) return -1;
  return 0;
}

static void print_usage() {
  printf("Group Scholar Funding Runway\n");
  printf("Usage: funding-runway --file path.csv --starting-cash 500000 [options]\n\n");
  printf("Options:\n");
  printf("  --file PATH             CSV file with date, amount, type, category, restricted\n");
  printf("  --starting-cash AMOUNT  Starting available cash balance\n");
  printf("  --reserved-cash AMOUNT  Reserved/restricted cash to exclude from runway\n");
  printf("  --window MONTHS         Use last N months for average burn calculation\n");
  printf("  --as-of YYYY-MM         Ignore transactions after a given month\n");
  printf("  --json PATH             Write JSON report to PATH\n");
  printf("  --help                  Show this help\n");
}

static double parse_amount(const char *value, int *ok) {
  char buf[64];
  size_t j = 0;
  int negative = 0;
  int saw_digit = 0;

  for (size_t i = 0; value[i] != '\0' && j + 1 < sizeof(buf); i++) {
    char c = value[i];
    if (c == '(') {
      negative = 1;
      continue;
    }
    if (c == ')') {
      continue;
    }
    if (c == '-') {
      negative = 1;
      continue;
    }
    if (c == '+' || c == '$' || c == ',' || isspace((unsigned char)c)) {
      continue;
    }
    if (isdigit((unsigned char)c) || c == '.') {
      buf[j++] = c;
      if (isdigit((unsigned char)c)) {
        saw_digit = 1;
      }
    }
  }

  buf[j] = '\0';
  if (!saw_digit) {
    *ok = 0;
    return 0.0;
  }

  char *endptr;
  double amt = strtod(buf, &endptr);
  if (endptr == buf) {
    *ok = 0;
    return 0.0;
  }

  *ok = 1;
  if (negative) {
    amt = -amt;
  }
  return amt;
}

int main(int argc, char **argv) {
  const char *file_path = NULL;
  const char *json_path = NULL;
  double starting_cash = 0.0;
  double reserved_cash = 0.0;
  int window_months = 0;
  char as_of[8] = "";
  int starting_cash_set = 0;

  for (int i = 1; i < argc; i++) {
    if (strcmp(argv[i], "--file") == 0 && i + 1 < argc) {
      file_path = argv[++i];
    } else if (strcmp(argv[i], "--starting-cash") == 0 && i + 1 < argc) {
      int ok = 0;
      starting_cash = parse_amount(argv[++i], &ok);
      if (!ok) {
        fprintf(stderr, "Invalid starting cash amount.\n");
        return 1;
      }
      starting_cash_set = 1;
    } else if (strcmp(argv[i], "--reserved-cash") == 0 && i + 1 < argc) {
      int ok = 0;
      reserved_cash = parse_amount(argv[++i], &ok);
      if (!ok) {
        fprintf(stderr, "Invalid reserved cash amount.\n");
        return 1;
      }
    } else if (strcmp(argv[i], "--window") == 0 && i + 1 < argc) {
      window_months = atoi(argv[++i]);
    } else if (strcmp(argv[i], "--as-of") == 0 && i + 1 < argc) {
      const char *value = argv[++i];
      if (strlen(value) != 7 || value[4] != '-' || !isdigit((unsigned char)value[0]) ||
          !isdigit((unsigned char)value[1]) || !isdigit((unsigned char)value[2]) ||
          !isdigit((unsigned char)value[3]) || !isdigit((unsigned char)value[5]) ||
          !isdigit((unsigned char)value[6])) {
        fprintf(stderr, "Invalid --as-of value. Use YYYY-MM.\n");
        return 1;
      }
      strncpy(as_of, value, sizeof(as_of) - 1);
      as_of[7] = '\0';
    } else if (strcmp(argv[i], "--json") == 0 && i + 1 < argc) {
      json_path = argv[++i];
    } else if (strcmp(argv[i], "--help") == 0) {
      print_usage();
      return 0;
    } else {
      printf("Unknown argument: %s\n", argv[i]);
      print_usage();
      return 1;
    }
  }

  if (!file_path || !starting_cash_set) {
    print_usage();
    return 1;
  }

  FILE *fp = fopen(file_path, "r");
  if (!fp) {
    fprintf(stderr, "Failed to open file: %s\n", file_path);
    return 1;
  }

  char line[MAX_LINE];
  char fields[MAX_FIELDS][MAX_FIELD_LEN];
  int header_parsed = 0;
  int idx_date = -1, idx_amount = -1, idx_type = -1, idx_category = -1, idx_restricted = -1;

  MonthList months = {0};
  CategoryList categories = {0};
  CategoryList inflow_categories = {0};

  size_t record_count = 0;
  size_t skipped = 0;
  double total_inflow = 0.0;
  double total_outflow = 0.0;
  double total_restricted = 0.0;

  while (fgets(line, sizeof(line), fp)) {
    int field_count = parse_csv_line(line, fields, MAX_FIELDS);
    if (!header_parsed) {
      for (int i = 0; i < field_count; i++) {
        char key[MAX_FIELD_LEN];
        normalize_key(fields[i], key, sizeof(key));
        if (strcmp(key, "date") == 0 || strcmp(key, "transactiondate") == 0 || strcmp(key, "txn") == 0 || strcmp(key, "txndate") == 0) {
          idx_date = i;
        } else if (strcmp(key, "amount") == 0 || strcmp(key, "value") == 0 || strcmp(key, "net") == 0) {
          idx_amount = i;
        } else if (strcmp(key, "type") == 0 || strcmp(key, "direction") == 0 || strcmp(key, "flow") == 0) {
          idx_type = i;
        } else if (strcmp(key, "category") == 0 || strcmp(key, "memo") == 0 || strcmp(key, "bucket") == 0) {
          idx_category = i;
        } else if (strcmp(key, "restricted") == 0 || strcmp(key, "restrictedflag") == 0 || strcmp(key, "restrictedfunds") == 0) {
          idx_restricted = i;
        }
      }
      header_parsed = 1;
      if (idx_date == -1 || idx_amount == -1 || idx_type == -1 || idx_category == -1) {
        fprintf(stderr, "Missing required headers. Need date, amount, type, category.\n");
        fclose(fp);
        return 1;
      }
      continue;
    }

    if (field_count <= idx_amount || field_count <= idx_date) {
      skipped++;
      continue;
    }

    int ok = 0;
    double amount = parse_amount(fields[idx_amount], &ok);
    if (!ok) {
      skipped++;
      continue;
    }

    const char *date = fields[idx_date];
    if (strlen(date) < 7) {
      skipped++;
      continue;
    }

    char month[8];
    strncpy(month, date, 7);
    month[7] = '\0';

    if (as_of[0] != '\0' && strcmp(month, as_of) > 0) {
      skipped++;
      continue;
    }

    const char *type = fields[idx_type];
    int is_inflow = 0;
    if (is_inflow_type(type)) {
      is_inflow = 1;
    } else if (is_outflow_type(type)) {
      is_inflow = 0;
    } else if (amount < 0) {
      is_inflow = 0;
      amount = -amount;
    } else {
      is_inflow = 1;
    }

    const char *category = idx_category >= 0 && idx_category < field_count ? fields[idx_category] : "Uncategorized";
    int restricted = 0;
    if (idx_restricted >= 0 && idx_restricted < field_count) {
      restricted = is_truthy(fields[idx_restricted]);
    }

    record_count++;

    if (is_inflow) {
      total_inflow += amount;
      month_list_add(&months, month, amount, 0.0);
      category_list_add(&inflow_categories, category[0] ? category : "Uncategorized", amount);
    } else {
      total_outflow += amount;
      month_list_add(&months, month, 0.0, amount);
      category_list_add(&categories, category[0] ? category : "Uncategorized", amount);
      if (restricted) {
        total_restricted += amount;
      }
    }
  }

  fclose(fp);

  qsort(months.items, months.count, sizeof(MonthStat), compare_months);
  qsort(categories.items, categories.count, sizeof(CategoryStat), compare_categories);
  qsort(inflow_categories.items, inflow_categories.count, sizeof(CategoryStat), compare_categories);

  double net = total_inflow - total_outflow;
  double available_cash = starting_cash - reserved_cash;
  if (available_cash < 0) available_cash = 0.0;

  double *month_net = NULL;
  double *month_balance = NULL;
  double ending_cash = available_cash;
  double lowest_balance = available_cash;
  char lowest_balance_month[8] = "";
  double peak_inflow = 0.0;
  double peak_outflow = 0.0;
  char peak_inflow_month[8] = "";
  char peak_outflow_month[8] = "";
  int deficit_months = 0;
  if (months.count > 0) {
    month_net = calloc(months.count, sizeof(double));
    month_balance = calloc(months.count, sizeof(double));
    if (!month_net || !month_balance) {
      fprintf(stderr, "Memory allocation failed for balances.\n");
      free(month_net);
      free(month_balance);
      free(months.items);
      free(categories.items);
      return 1;
    }
    double balance = available_cash;
    for (size_t i = 0; i < months.count; i++) {
      month_net[i] = months.items[i].inflow - months.items[i].outflow;
      balance += month_net[i];
      month_balance[i] = balance;
      if (month_net[i] < 0) {
        deficit_months++;
      }
      if (i == 0 || balance < lowest_balance) {
        lowest_balance = balance;
        strncpy(lowest_balance_month, months.items[i].month, sizeof(lowest_balance_month) - 1);
        lowest_balance_month[7] = '\0';
      }
      if (i == 0 || months.items[i].inflow > peak_inflow) {
        peak_inflow = months.items[i].inflow;
        strncpy(peak_inflow_month, months.items[i].month, sizeof(peak_inflow_month) - 1);
        peak_inflow_month[7] = '\0';
      }
      if (i == 0 || months.items[i].outflow > peak_outflow) {
        peak_outflow = months.items[i].outflow;
        strncpy(peak_outflow_month, months.items[i].month, sizeof(peak_outflow_month) - 1);
        peak_outflow_month[7] = '\0';
      }
    }
    ending_cash = month_balance[months.count - 1];
  }

  size_t month_start = 0;
  if (window_months > 0 && months.count > (size_t)window_months) {
    month_start = months.count - (size_t)window_months;
  }

  double burn_total = 0.0;
  int burn_count = 0;
  double net_total = 0.0;
  double inflow_total = 0.0;
  double outflow_total = 0.0;
  int net_count = 0;
  for (size_t i = month_start; i < months.count; i++) {
    double month_net = months.items[i].inflow - months.items[i].outflow;
    net_total += month_net;
    inflow_total += months.items[i].inflow;
    outflow_total += months.items[i].outflow;
    net_count++;
    if (month_net < 0) {
      burn_total += -month_net;
      burn_count++;
    }
  }

  double avg_burn = burn_count > 0 ? burn_total / burn_count : 0.0;
  double avg_net = net_count > 0 ? net_total / net_count : 0.0;
  double avg_inflow = net_count > 0 ? inflow_total / net_count : 0.0;
  double avg_outflow = net_count > 0 ? outflow_total / net_count : 0.0;
  double outflow_coverage = avg_outflow > 0 ? available_cash / avg_outflow : 0.0;
  double net_variance_sum = 0.0;
  if (net_count > 0) {
    for (size_t i = month_start; i < months.count; i++) {
      double month_net = months.items[i].inflow - months.items[i].outflow;
      double diff = month_net - avg_net;
      net_variance_sum += diff * diff;
    }
  }
  double net_volatility = net_count > 0 ? sqrt(net_variance_sum / net_count) : 0.0;
  double runway_months = avg_burn > 0 ? available_cash / avg_burn : 0.0;
  const char *risk_level = "not_at_risk";
  if (avg_burn > 0) {
    if (runway_months < 3.0) {
      risk_level = "critical";
    } else if (runway_months < 6.0) {
      risk_level = "high";
    } else if (runway_months < 12.0) {
      risk_level = "moderate";
    } else {
      risk_level = "stable";
    }
  }
  size_t trend_window = 3;
  size_t recent_start = months.count > trend_window ? months.count - trend_window : 0;
  size_t recent_count = months.count - recent_start;
  double recent_net_total = 0.0;
  for (size_t i = recent_start; i < months.count; i++) {
    recent_net_total += months.items[i].inflow - months.items[i].outflow;
  }
  double recent_avg_net = recent_count > 0 ? recent_net_total / (double)recent_count : 0.0;
  size_t prior_end = recent_start;
  size_t prior_start = prior_end > trend_window ? prior_end - trend_window : 0;
  size_t prior_count = prior_end - prior_start;
  double prior_net_total = 0.0;
  for (size_t i = prior_start; i < prior_end; i++) {
    prior_net_total += months.items[i].inflow - months.items[i].outflow;
  }
  double prior_avg_net = prior_count > 0 ? prior_net_total / (double)prior_count : 0.0;
  double net_trend_delta = recent_avg_net - prior_avg_net;
  double net_trend_abs = fabs(net_trend_delta);

  printf("Group Scholar Funding Runway\n");
  printf("Records: %zu | Months: %zu | Skipped: %zu\n", record_count, months.count, skipped);
  printf("Totals: Inflow $%.2f | Outflow $%.2f | Net $%.2f\n", total_inflow, total_outflow, net);
  printf("Starting cash: $%.2f | Reserved cash: $%.2f | Available: $%.2f\n", starting_cash, reserved_cash, available_cash);
  printf("Ending cash (as of last month): $%.2f\n", ending_cash);
  if (months.count > 0) {
    printf("Lowest cash balance: $%.2f (%s)\n", lowest_balance, lowest_balance_month);
    printf("Peak inflow month: %s ($%.2f)\n", peak_inflow_month, peak_inflow);
    printf("Peak outflow month: %s ($%.2f)\n", peak_outflow_month, peak_outflow);
    printf("Deficit months: %d\n", deficit_months);
  }
  if (avg_burn > 0) {
    printf("Average monthly burn (negative net): $%.2f across %d months\n", avg_burn, burn_count);
    printf("Average monthly net: $%.2f across %d months\n", avg_net, net_count);
    printf("Average monthly inflow: $%.2f | Outflow: $%.2f\n", avg_inflow, avg_outflow);
    printf("Net volatility (std dev): $%.2f\n", net_volatility);
    printf("Recent %zu-month average net: $%.2f\n", recent_count, recent_avg_net);
    printf("Estimated runway: %.1f months\n", runway_months);
    printf("Runway risk: %s\n", risk_level);
  } else {
    printf("Average monthly burn: $0.00 (no negative net months)\n");
    printf("Average monthly net: $%.2f across %d months\n", avg_net, net_count);
    printf("Average monthly inflow: $%.2f | Outflow: $%.2f\n", avg_inflow, avg_outflow);
    printf("Net volatility (std dev): $%.2f\n", net_volatility);
    printf("Recent %zu-month average net: $%.2f\n", recent_count, recent_avg_net);
    printf("Estimated runway: Not at risk based on current net flow\n");
    printf("Runway risk: %s\n", risk_level);
  }
  if (avg_outflow > 0) {
    printf("Outflow coverage: %.1f months of average spend\n", outflow_coverage);
  }
  if (prior_count > 0) {
    printf("Prior %zu-month average net: $%.2f\n", prior_count, prior_avg_net);
    printf("Net trend: %s $%.2f\n", net_trend_delta >= 0 ? "improving by" : "declining by", net_trend_abs);
  } else {
    printf("Net trend: Not enough history for comparison\n");
  }
  if (total_restricted > 0) {
    printf("Restricted outflow total: $%.2f\n", total_restricted);
  }

  printf("\nRecent months:\n");
  size_t recent_display_start = months.count > 6 ? months.count - 6 : 0;
  for (size_t i = recent_display_start; i < months.count; i++) {
    double month_net_value = month_net ? month_net[i] : months.items[i].inflow - months.items[i].outflow;
    double month_balance_value = month_balance ? month_balance[i] : available_cash + month_net_value;
    printf("  %s | In $%.2f | Out $%.2f | Net $%.2f | Bal $%.2f\n",
           months.items[i].month, months.items[i].inflow, months.items[i].outflow, month_net_value, month_balance_value);
  }

  if (categories.count > 0) {
    printf("\nTop outflow categories:\n");
    size_t top = categories.count > 5 ? 5 : categories.count;
    for (size_t i = 0; i < top; i++) {
      double share = total_outflow > 0 ? (categories.items[i].outflow / total_outflow) * 100.0 : 0.0;
      printf("  %s | $%.2f (%d items, %.1f%% of outflow)\n",
             categories.items[i].name, categories.items[i].outflow, categories.items[i].count, share);
    }
  }
  if (inflow_categories.count > 0) {
    printf("\nTop inflow categories:\n");
    size_t top = inflow_categories.count > 5 ? 5 : inflow_categories.count;
    for (size_t i = 0; i < top; i++) {
      double share = total_inflow > 0 ? (inflow_categories.items[i].outflow / total_inflow) * 100.0 : 0.0;
      printf("  %s | $%.2f (%d items, %.1f%% of inflow)\n",
             inflow_categories.items[i].name, inflow_categories.items[i].outflow,
             inflow_categories.items[i].count, share);
    }
  }

  if (json_path) {
    FILE *out = fopen(json_path, "w");
    if (!out) {
      fprintf(stderr, "Failed to write JSON to %s\n", json_path);
    } else {
      fprintf(out, "{\n");
      fprintf(out, "  \"records\": %zu,\n", record_count);
      fprintf(out, "  \"months\": %zu,\n", months.count);
      fprintf(out, "  \"skipped\": %zu,\n", skipped);
      fprintf(out, "  \"totals\": {\n");
      fprintf(out, "    \"inflow\": %.2f,\n", total_inflow);
      fprintf(out, "    \"outflow\": %.2f,\n", total_outflow);
      fprintf(out, "    \"net\": %.2f\n", net);
      fprintf(out, "  },\n");
      fprintf(out, "  \"cash\": {\n");
      fprintf(out, "    \"starting\": %.2f,\n", starting_cash);
      fprintf(out, "    \"reserved\": %.2f,\n", reserved_cash);
      fprintf(out, "    \"available\": %.2f\n", available_cash);
      fprintf(out, "  },\n");
      fprintf(out, "  \"cash_flow\": {\n");
      fprintf(out, "    \"ending_balance\": %.2f,\n", ending_cash);
      fprintf(out, "    \"lowest_balance\": %.2f,\n", lowest_balance);
      fprintf(out, "    \"lowest_balance_month\": \"%s\",\n", months.count > 0 ? lowest_balance_month : "");
      fprintf(out, "    \"peak_inflow\": %.2f,\n", peak_inflow);
      fprintf(out, "    \"peak_inflow_month\": \"%s\",\n", months.count > 0 ? peak_inflow_month : "");
      fprintf(out, "    \"peak_outflow\": %.2f,\n", peak_outflow);
      fprintf(out, "    \"peak_outflow_month\": \"%s\",\n", months.count > 0 ? peak_outflow_month : "");
      fprintf(out, "    \"deficit_months\": %d\n", deficit_months);
      fprintf(out, "  },\n");
      fprintf(out, "  \"as_of\": \"%s\",\n", as_of[0] ? as_of : "");
      fprintf(out, "  \"window_months\": %d,\n", window_months);
      fprintf(out, "  \"runway_risk\": \"%s\",\n", risk_level);
      fprintf(out, "  \"burn\": {\n");
      fprintf(out, "    \"average_monthly\": %.2f,\n", avg_burn);
      fprintf(out, "    \"months_used\": %d,\n", burn_count);
      fprintf(out, "    \"estimated_runway_months\": %.2f\n", runway_months);
      fprintf(out, "  },\n");
      fprintf(out, "  \"flows\": {\n");
      fprintf(out, "    \"average_inflow\": %.2f,\n", avg_inflow);
      fprintf(out, "    \"average_outflow\": %.2f,\n", avg_outflow);
      fprintf(out, "    \"outflow_coverage_months\": %.2f\n", outflow_coverage);
      fprintf(out, "  },\n");
      fprintf(out, "  \"net\": {\n");
      fprintf(out, "    \"average_monthly\": %.2f,\n", avg_net);
      fprintf(out, "    \"months_used\": %d,\n", net_count);
      fprintf(out, "    \"volatility\": %.2f\n", net_volatility);
      fprintf(out, "  },\n");
      fprintf(out, "  \"net_trend\": {\n");
      fprintf(out, "    \"window_months\": %zu,\n", trend_window);
      fprintf(out, "    \"recent_average\": %.2f,\n", recent_avg_net);
      fprintf(out, "    \"recent_months\": %zu,\n", recent_count);
      fprintf(out, "    \"prior_average\": %.2f,\n", prior_avg_net);
      fprintf(out, "    \"prior_months\": %zu,\n", prior_count);
      fprintf(out, "    \"delta\": %.2f\n", net_trend_delta);
      fprintf(out, "  },\n");
      fprintf(out, "  \"restricted\": {\n");
      fprintf(out, "    \"outflow_total\": %.2f\n", total_restricted);
      fprintf(out, "  },\n");
      fprintf(out, "  \"recent_months\": [\n");
      for (size_t i = recent_start; i < months.count; i++) {
        double month_net_value = month_net ? month_net[i] : months.items[i].inflow - months.items[i].outflow;
        fprintf(out, "    {\"month\": \"%s\", \"inflow\": %.2f, \"outflow\": %.2f, \"net\": %.2f}%s\n",
                months.items[i].month, months.items[i].inflow, months.items[i].outflow, month_net_value,
                i + 1 < months.count ? "," : "");
      }
      fprintf(out, "  ],\n");
      fprintf(out, "  \"month_balances\": [\n");
      for (size_t i = 0; i < months.count; i++) {
        double month_net_value = month_net ? month_net[i] : months.items[i].inflow - months.items[i].outflow;
        double month_balance_value = month_balance ? month_balance[i] : available_cash + month_net_value;
        fprintf(out, "    {\"month\": \"%s\", \"inflow\": %.2f, \"outflow\": %.2f, \"net\": %.2f, \"balance\": %.2f}%s\n",
                months.items[i].month, months.items[i].inflow, months.items[i].outflow,
                month_net_value, month_balance_value, i + 1 < months.count ? "," : "");
      }
      fprintf(out, "  ],\n");
      fprintf(out, "  \"top_categories\": [\n");
      size_t top = categories.count > 5 ? 5 : categories.count;
      for (size_t i = 0; i < top; i++) {
        double share = total_outflow > 0 ? (categories.items[i].outflow / total_outflow) * 100.0 : 0.0;
        fprintf(out, "    {\"category\": \"%s\", \"outflow\": %.2f, \"count\": %d, \"share_of_outflow\": %.2f}%s\n",
                categories.items[i].name, categories.items[i].outflow, categories.items[i].count, share,
                i + 1 < top ? "," : "");
      }
      fprintf(out, "  ],\n");
      fprintf(out, "  \"top_inflow_categories\": [\n");
      size_t inflow_top = inflow_categories.count > 5 ? 5 : inflow_categories.count;
      for (size_t i = 0; i < inflow_top; i++) {
        double share = total_inflow > 0 ? (inflow_categories.items[i].outflow / total_inflow) * 100.0 : 0.0;
        fprintf(out, "    {\"category\": \"%s\", \"inflow\": %.2f, \"count\": %d, \"share_of_inflow\": %.2f}%s\n",
                inflow_categories.items[i].name, inflow_categories.items[i].outflow,
                inflow_categories.items[i].count, share,
                i + 1 < inflow_top ? "," : "");
      }
      fprintf(out, "  ]\n");
      fprintf(out, "}\n");
      fclose(out);
      printf("\nJSON report written to %s\n", json_path);
    }
  }

  free(months.items);
  free(categories.items);
  free(month_net);
  free(month_balance);
  free(inflow_categories.items);
  return 0;
}
