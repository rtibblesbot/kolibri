package org.learningequality.Kolibri.discovery;

import android.content.Context;
import androidx.annotation.VisibleForTesting;
import java.net.InetSocketAddress;
import java.net.NetworkInterface;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;
import org.learningequality.Kolibri.util.ContextUtil;
import org.learningequality.Kolibri.util.NetworkUtils;

public final class ServerDiscovery {

  static final String SERVICE_NAME = "Kolibri._sub._http._tcp.local.";
  static final long DISCOVERY_WINDOW_MS = 3000;
  static final long QUERY_INTERVAL_MS = 1000;

  private static final InetSocketAddress MDNS_GROUP = new InetSocketAddress("224.0.0.251", 5353);

  private static volatile ServerDiscovery instance;

  private final Context context;
  private final InetSocketAddress group;
  private final Supplier<List<NetworkInterface>> interfaces;
  private final Supplier<Collection<String>> ownAddresses;

  @VisibleForTesting
  ServerDiscovery(
      Context context,
      InetSocketAddress group,
      Supplier<List<NetworkInterface>> interfaces,
      Supplier<Collection<String>> ownAddresses) {
    this.context = context;
    this.group = group;
    this.interfaces = interfaces;
    this.ownAddresses = ownAddresses;
  }

  public static ServerDiscovery getInstance() {
    if (instance == null) {
      synchronized (ServerDiscovery.class) {
        if (instance == null) {
          instance =
              new ServerDiscovery(
                  ContextUtil.getApplicationContext(),
                  MDNS_GROUP,
                  NetworkUtils::getActiveIPv4Interfaces,
                  NetworkUtils::getActiveIPv4Addresses);
        }
      }
    }
    return instance;
  }

  @VisibleForTesting
  public static void setInstanceForTesting(ServerDiscovery discovery) {
    instance = discovery;
  }

  /** Calls back once, off the UI thread, with the eligible servers found. */
  public void discover(Consumer<List<DiscoveredServer>> callback) {
    callback.accept(Collections.emptyList());
  }
}
